import os
import geopandas as gpd
import networkx as nx
from collections import defaultdict, Counter
import pandas as pd

def load_category_hierarchy(csv_path):
    """Load category hierarchy data"""
    hierarchy_dict = {}
    with open(csv_path, 'r', encoding='utf-8') as f:
        next(f)  # Skip header line
        for line in f:
            code, taxonomy = line.strip().split(';')
            code = code.strip()
            # Convert string form list to actual list
            taxonomy = taxonomy.strip()
            taxonomy = taxonomy.replace('[', '').replace(']', '')  # Remove brackets
            taxonomy = [item.strip() for item in taxonomy.split(',')]  # Split and clean each item
            hierarchy_dict[code] = taxonomy
    return hierarchy_dict

def get_category_at_level(category_code, hierarchy_dict, level=1):
    """Get category name at specified level"""
    if category_code not in hierarchy_dict:
        return category_code
    
    taxonomy = hierarchy_dict[category_code]
    if level <= len(taxonomy):
        return taxonomy[level-1]
    return taxonomy[-1]

def clean_category(category):
    """Clean category name, remove spaces etc."""
    return category.strip() if category else category

def get_category_hierarchy_info(category_code, hierarchy_dict, target_level=1):
    """Get category hierarchy information"""
    if category_code not in hierarchy_dict:
        return {
            'name': category_code,
            **{f'type{i+1}': category_code for i in range(target_level)}
        }
    
    taxonomy = hierarchy_dict[category_code]
    result = {'name': taxonomy[min(target_level-1, len(taxonomy)-1)]}
    
    # Add all upper level category information
    for i in range(target_level):
        if i < len(taxonomy):
            result[f'type{i+1}'] = taxonomy[i]
        else:
            result[f'type{i+1}'] = taxonomy[-1]
    
    return result

def create_category_network(gdf, hierarchy_dict, level=1):
    """Create category network, supports selecting taxonomy level"""
    G = nx.Graph()
    edge_weights = defaultdict(int)
    
    # Iterate through each road's category chain
    for chain in gdf['categories_primary_chain']:
        if not isinstance(chain, str):
            continue
            
        # Split and clean category chain
        categories = [clean_category(cat) for cat in chain.split('|')]
        categories = [cat for cat in categories if cat]
        
        # Create edge connections
        for i in range(len(categories)-1):
            if categories[i] and categories[i+1]:
                # Get hierarchy info for both nodes
                node1_info = get_category_hierarchy_info(categories[i], hierarchy_dict, level)
                node2_info = get_category_hierarchy_info(categories[i+1], hierarchy_dict, level)
                
                # Use target level name as node identifier
                node1_name = node1_info['name']
                node2_name = node2_info['name']
                
                # Sort nodes alphabetically to ensure edge consistency
                if node1_name > node2_name:
                    node1_name, node2_name = node2_name, node1_name
                    node1_info, node2_info = node2_info, node1_info
                
                # Add nodes and their attributes
                G.add_node(node1_name, **node1_info)
                G.add_node(node2_name, **node2_info)
                
                edge = (node1_name, node2_name)
                edge_weights[edge] += 1
    
    # Add edges and weights to graph
    for (node1, node2), weight in edge_weights.items():
        G.add_edge(node1, node2, weight=weight)
    
    return G

def count_category_occurrences(gdf):
    """Count total occurrences of each category in dataset"""
    all_categories = []
    for chain in gdf['categories_primary_chain']:
        if isinstance(chain, str):
            categories = [clean_category(cat) for cat in chain.split('|')]
            all_categories.extend(cat for cat in categories if cat)
    return Counter(all_categories)

def generate_network_report(G, gdf, output_path):
    """Generate network analysis report"""
    with open(output_path, 'w', encoding='utf-8') as f:

        # Add node attribute information
        f.write("\n=== Node Type Information ===\n")
        for node in list(G.nodes())[:10]:  # Show first 10 nodes as examples
            f.write(f"\nNode: {node}\n")
            for key, value in G.nodes[node].items():
                if key != 'name':  # name already shown
                    f.write(f"  {key}: {value}\n")
        f.write("\n")

        # 1. Category frequency statistics
        f.write("=== Top 10 Most Frequent Categories ===\n")
        category_counts = count_category_occurrences(gdf)
        for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            f.write(f"{cat}: {count}\n")
        f.write("\n")

        # 2. Degree centrality
        f.write("=== Top 10 Nodes by Degree Centrality ===\n")
        degree_cent = nx.degree_centrality(G)
        for node, cent in sorted(degree_cent.items(), key=lambda x: x[1], reverse=True)[:10]:
            degree = G.degree(node)
            f.write(f"{node}: {cent:.4f} (degree: {degree})\n")
        f.write("\n")

        # 3. Betweenness centrality
        f.write("=== Top 10 Nodes by Betweenness Centrality ===\n")
        between_cent = nx.betweenness_centrality(G)
        for node, cent in sorted(between_cent.items(), key=lambda x: x[1], reverse=True)[:10]:
            f.write(f"{node}: {cent:.4f}\n")
        f.write("\n")

        # 4. Closeness centrality
        f.write("=== Top 10 Nodes by Closeness Centrality ===\n")
        close_cent = nx.closeness_centrality(G)
        for node, cent in sorted(close_cent.items(), key=lambda x: x[1], reverse=True)[:10]:
            f.write(f"{node}: {cent:.4f}\n")
        f.write("\n")

        # 5. Highest weight edges
        f.write("=== Top 10 Edges by Weight ===\n")
        edges = [(u, v, d['weight']) for u, v, d in G.edges(data=True)]
        for u, v, w in sorted(edges, key=lambda x: x[2], reverse=True)[:10]:
            f.write(f"{u} -- {v}: {w}\n")
        f.write("\n")

        # Additional network metrics
        f.write("=== Additional Network Metrics ===\n")
        
        # 6. Overall network density
        density = nx.density(G)
        f.write(f"Network Density: {density:.4f}\n")
        
        # 7. Average clustering coefficient
        avg_clustering = nx.average_clustering(G)
        f.write(f"Average Clustering Coefficient: {avg_clustering:.4f}\n")
        
        # 8. Network diameter
        diameter = nx.diameter(G)
        f.write(f"Network Diameter: {diameter}\n")
        
        # 9. Average shortest path length
        avg_path_length = nx.average_shortest_path_length(G)
        f.write(f"Average Shortest Path Length: {avg_path_length:.4f}\n")
        
        # 10. Community detection (Louvain method)
        try:
            import community
            communities = community.best_partition(G)
            num_communities = len(set(communities.values()))
            f.write(f"Number of Communities (Louvain): {num_communities}\n")
        except ImportError:
            f.write("Community detection requires python-louvain package\n")
        
        # 11. Assortativity coefficient
        assortativity = nx.degree_assortativity_coefficient(G)
        f.write(f"Degree Assortativity Coefficient: {assortativity:.4f}\n")

def main():
    # Read data
    # Standalone example for a single city (run 03_generate_chains.py first)
    out_dir = "data/output/chainAnalysisData/amsterdam"
    os.makedirs(out_dir, exist_ok=True)
    gdf = gpd.read_file("data/output/chainRawData/amsterdam/amsterdam_road_text_chain.geojson")
    
    # Load category hierarchy data
    hierarchy_dict = load_category_hierarchy("data/input/overture_categories.csv")
    
    # Create network (can select level: 1 for first level, 2 for second level, etc.)
    level = 2  # Level can be modified here
    category_network = create_category_network(gdf, hierarchy_dict, level)
    
    # Generate report
    generate_network_report(category_network, gdf, 
                          os.path.join(out_dir, f"network_report_level_{level}.txt"))
    
    # Save network data (GraphML format can save node attributes)
    nx.write_graphml(category_network, 
                    os.path.join(out_dir, f"category_network_level_{level}.graphml"))
    
    # Print basic statistics
    print(f"Number of nodes: {category_network.number_of_nodes()}")
    print(f"Number of edges: {category_network.number_of_edges()}")

if __name__ == "__main__":
    main()
