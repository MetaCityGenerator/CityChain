"""
Study cities and their bounding boxes.

bbox format: (min_lon, min_lat, max_lon, max_lat) in EPSG:4326.
Keys are used as folder / file-name prefixes under data/input/city/<key>/.
Add or remove entries here to change which cities are downloaded and clipped.
"""

CITIES = {
    # Major cities in developed countries
    "new_york": {
        "name": "New York City",
        "bbox": (-74.25559, 40.49612, -73.70001, 40.91589)
    },
    "san_francisco": {
        "name": "San Francisco",
        "bbox": (-122.5158, 37.7079, -122.3558, 37.8324)
    },
    "toronto": {
        "name": "Toronto",
        "bbox": (-79.639219, 43.580996, -79.115623, 43.855517)
    },
    "london": {
        "name": "London",
        "bbox": (-0.5103, 51.2867, 0.3340, 51.6918)
    },
    "paris": {
        "name": "Paris",
        "bbox": (2.224199, 48.815573, 2.469921, 48.902145)
    },
    "amsterdam": {
        "name": "Amsterdam",
        "bbox": (4.728758, 52.278174, 5.068625, 52.431823)
    },
    "vienna": {
        "name": "Vienna",
        "bbox": (16.182557, 48.117666, 16.577510, 48.322506)
    },
    "tokyo": {
        "name": "Tokyo",
        "bbox": (139.5916, 35.5320, 139.9216, 35.8187)
    },
    "seoul": {
        "name": "Seoul",
        "bbox": (126.764957, 37.428387, 127.183503, 37.701389)
    },
    "singapore": {
        "name": "Singapore",
        "bbox": (103.602340, 1.209596, 104.088771, 1.471328)
    },

    # Major cities in developing countries
    "beijing": {
        "name": "Beijing",
        "bbox": (115.4, 39.4, 117.5, 41.1)
    },
    "mumbai": {
        "name": "Mumbai",
        "bbox": (72.775841, 18.892443, 72.995764, 19.270737)
    },
    "bangkok": {
        "name": "Bangkok",
        "bbox": (100.327873, 13.494361, 100.938403, 13.955219)
    },
    "jakarta": {
        "name": "Jakarta",
        "bbox": (106.681982, -6.372699, 107.052896, -6.074226)
    },
    "manila": {
        "name": "Manila",
        "bbox": (120.901470, 14.351455, 121.101506, 14.761531)
    },
    "sao_paulo": {
        "name": "São Paulo",
        "bbox": (-46.825514, -24.008814, -46.365728, -23.356792)
    },
    "mexico_city": {
        "name": "Mexico City",
        "bbox": (-99.352846, 19.048611, -98.883029, 19.592757)
    },
    "lima": {
        "name": "Lima",
        "bbox": (-77.197981, -12.377513, -76.701037, -11.816507)
    },
    "cairo": {
        "name": "Cairo",
        "bbox": (31.222897, 29.951908, 31.576552, 30.164953)
    },
    "lagos": {
        "name": "Lagos",
        "bbox": (3.142704, 6.393351, 3.485687, 6.701593)
    },

    # Medium-sized cities
    "porto": {
        "name": "Porto",
        "bbox": (-8.688889, 41.140576, -8.560784, 41.185143)
    },
    "lyon": {
        "name": "Lyon",
        "bbox": (4.771843, 45.707320, 4.898787, 45.808188)
    },
    "munich": {
        "name": "Munich",
        "bbox": (11.360269, 48.061743, 11.723807, 48.248781)
    },
    "milan": {
        "name": "Milan",
        "bbox": (9.065723, 45.398767, 9.278975, 45.535839)
    },
    "fukuoka": {
        "name": "Fukuoka",
        "bbox": (130.327554, 33.557048, 130.448618, 33.674347)
    },
    "qingdao": {
        "name": "Qingdao",
        "bbox": (120.197665, 36.039846, 120.478548, 36.239391)
    },
    "taipei": {
        "name": "Taipei",
        "bbox": (121.457971, 24.960098, 121.665338, 25.211004)
    },
    "bangalore": {
        "name": "Bangalore",
        "bbox": (77.469504, 12.864352, 77.747566, 13.139784)
    },
    "portland": {
        "name": "Portland",
        "bbox": (-122.836925, 45.432536, -122.472701, 45.652741)
    },
    "montreal": {
        "name": "Montreal",
        "bbox": (-73.976268, 45.410012, -73.473123, 45.704589)
    },
    "medellin": {
        "name": "Medellín",
        "bbox": (-75.640974, 6.168226, -75.504847, 6.382777)
    },
    "guadalajara": {
        "name": "Guadalajara",
        "bbox": (-103.406037, 20.559938, -103.238366, 20.755534)
    },

    # Distinctive small cities
    "freiburg": {
        "name": "Freiburg",
        "bbox": (7.785296, 47.957976, 7.901811, 48.026751)
    },
    "cambridge_uk": {
        "name": "Cambridge",
        "bbox": (0.068712, 52.159987, 0.186987, 52.237946)
    },
    "ljubljana": {
        "name": "Ljubljana",
        "bbox": (14.442368, 46.016561, 14.585575, 46.145882)
    },
    "lucerne": {
        "name": "Lucerne",
        "bbox": (8.243302, 47.021763, 8.363508, 47.096340)
    },
    "kyoto": {
        "name": "Kyoto",
        "bbox": (135.645243, 34.926861, 135.856942, 35.100677)
    },
    "kochi_japan": {
        "name": "Kochi",
        "bbox": (133.502096, 33.525291, 133.592691, 33.583891)
    },
    "utrecht": {
        "name": "Utrecht",
        "bbox": (5.079657, 52.058367, 5.176516, 52.133057)
    },
    "bordeaux": {
        "name": "Bordeaux",
        "bbox": (-0.637079, 44.808021, -0.528074, 44.894753)
    }
}
