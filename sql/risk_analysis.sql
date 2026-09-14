-- =====================================================================
-- ANÁLISE DE RISCO E COMPORTAMENTO DE ASTEROIDES (NEO NASA)
-- =====================================================================

-- 1. Resumo Executivo: Proporção de Asteroides Potencialmente Perigosos
-- Avalia o volume total, quantidade de perigosos e o percentual de risco da base.
SELECT 
    COUNT(*) AS total_asteroids,
    SUM(CASE WHEN is_potentially_hazardous_asteroid = 1 THEN 1 ELSE 0 END) AS hazardous_count,
    ROUND(
        (SUM(CASE WHEN is_potentially_hazardous_asteroid = 1 THEN 1 ELSE 0 END) * 100.0) / COUNT(*), 
        2
    ) AS hazardous_percentage,
    ROUND(AVG(estimated_diameter_max_km), 4) AS avg_max_diameter_km
FROM near_earth_objects;


-- 2. Análise Temporal: Média de Velocidade e Distância por Mês de Aproximação
-- Utiliza funções de agregação temporal para identificar padrões nas órbitas.
SELECT 
    STRFTIME('%Y-%m', close_approach_date) AS approach_month,
    COUNT(DISTINCT neo_reference_id) AS unique_asteroids_count,
    ROUND(AVG(relative_velocity_kmh), 2) AS avg_velocity_kmh,
    ROUND(MIN(miss_distance_km), 2) AS closest_miss_distance_km
FROM near_earth_objects
GROUP BY approach_month
ORDER BY approach_month ASC;


-- 3. Top Alvos Críticos: Ranking de Maior Risco por Proximidade e Velocidade
-- Identifica os 5 eventos com menor distância de passagem combinada com alta velocidade.
SELECT 
    name,
    close_approach_date,
    ROUND(miss_distance_km, 2) AS miss_distance_km,
    ROUND(relative_velocity_kmh, 2) AS relative_velocity_kmh,
    ROUND(estimated_diameter_max_km, 3) AS max_diameter_km,
    is_potentially_hazardous_asteroid
FROM near_earth_objects
WHERE miss_distance_km IS NOT NULL
ORDER BY miss_distance_km ASC, relative_velocity_kmh DESC
LIMIT 5;