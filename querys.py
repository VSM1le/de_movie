# -- Query 1: View Top 5 Most Popular Movies Today
# SELECT 
#     m.title, 
#     f.popularity, 
#     f.vote_average, 
#     f.extracted_at
# FROM fact_movie_popularity f
# JOIN dim_movies m ON f.movie_id = m.movie_id
# ORDER BY f.popularity DESC
# LIMIT 5;

# -- Query 2: Aggregate metric to check the count of top trending movies by language
# SELECT 
#     m.original_language, 
#     COUNT(DISTINCT m.movie_id) as movie_count,
#     ROUND(AVG(f.vote_average), 2) as average_rating
# FROM dim_movies m
# JOIN fact_movie_popularity f ON m.movie_id = f.movie_id
# GROUP BY m.original_language
# ORDER BY movie_count DESC;
