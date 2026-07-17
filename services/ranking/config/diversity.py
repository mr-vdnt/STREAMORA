# Diversity Limits Configuration
# Controls how many identical attributes can appear in the final recommendation list

DIVERSITY_LIMITS = {
    "MAX_SAME_FRANCHISE": 2,
    "MAX_SAME_DIRECTOR": 2,
    "MAX_SAME_ACTOR": 3,
    "MAX_SAME_GENRE": 5, # High limit for genre, since users usually search by genre
}
