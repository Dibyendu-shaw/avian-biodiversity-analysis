-- ==========================================================
-- AVIAN BIODIVERSITY & CONSERVATION ANALYTICAL QUERIES
-- Database: bird_monitoring.db | Table: bird_observations
-- ==========================================================

-- 1. Habitat Biodiversity & Conservation Density Comparison
SELECT 
    Location_Type,
    COUNT(Common_Name) AS Total_Observations,
    COUNT(DISTINCT Scientific_Name) AS Unique_Species,
    COUNT(DISTINCT Plot_Name) AS Active_Plots,
    SUM(CASE WHEN PIF_Watchlist_Status = 1 THEN 1 ELSE 0 END) AS Watchlist_Observations,
    ROUND(AVG(Temperature), 2) AS Avg_Temperature_C,
    ROUND(AVG(Humidity), 2) AS Avg_Humidity_Pct
FROM bird_observations
GROUP BY Location_Type;

-- 2. Top 5 Most Frequently Observed Species per Administrative Unit
WITH SpeciesCounts AS (
    SELECT 
        Admin_Unit_Code,
        Common_Name,
        Scientific_Name,
        COUNT(*) AS Sightings,
        DENSE_RANK() OVER (PARTITION BY Admin_Unit_Code ORDER BY COUNT(*) DESC) AS Rank_Position
    FROM bird_observations
    GROUP BY Admin_Unit_Code, Common_Name, Scientific_Name
)
SELECT 
    Admin_Unit_Code,
    Common_Name,
    Scientific_Name,
    Sightings
FROM SpeciesCounts
WHERE Rank_Position <= 5
ORDER BY Admin_Unit_Code, Sightings DESC;

-- 3. High-Priority Watchlist Species Threat & Habitat Profile
SELECT 
    Common_Name,
    Scientific_Name,
    Location_Type,
    COUNT(*) AS Sighting_Count,
    ROUND(AVG(CASE WHEN Temperature != 'None' THEN CAST(Temperature AS FLOAT) ELSE NULL END), 1) AS Mean_Temp_C,
    SUM(CASE WHEN Flyover_Observed = 1 THEN 1 ELSE 0 END) AS Flyover_Count
FROM bird_observations
WHERE PIF_Watchlist_Status = 1
GROUP BY Common_Name, Scientific_Name, Location_Type
ORDER BY Sighting_Count DESC
LIMIT 15;

-- 4. Diurnal Peak Activity Windows by Observation Hour
SELECT 
    CAST(SUBSTR(Start_Time, 1, INSTR(Start_Time, ':') - 1) AS INTEGER) AS Observation_Hour,
    Location_Type,
    COUNT(*) AS Observation_Count,
    COUNT(DISTINCT Scientific_Name) AS Species_Detected
FROM bird_observations
WHERE Start_Time IS NOT NULL AND Start_Time != 'None'
GROUP BY Observation_Hour, Location_Type
ORDER BY Observation_Hour ASC, Observation_Count DESC;

-- 5. Observer Detection Volume and Identification Distribution
SELECT 
    Observer,
    COUNT(*) AS Total_Records,
    COUNT(DISTINCT Scientific_Name) AS Unique_Species_Identified,
    SUM(CASE WHEN ID_Method = 'Singing' THEN 1 ELSE 0 END) AS Singing_Detections,
    SUM(CASE WHEN ID_Method = 'Visual' THEN 1 ELSE 0 END) AS Visual_Detections,
    SUM(CASE WHEN ID_Method = 'Calling' THEN 1 ELSE 0 END) AS Calling_Detections
FROM bird_observations
GROUP BY Observer
HAVING COUNT(*) > 50
ORDER BY Total_Records DESC;
