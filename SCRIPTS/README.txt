Hello , this is Bhavesh Gudlani author of this project explaining how all the scripts work and in which manner they should be run ::
(Note - Scripts folder is just for grouping purpose in realtime all script files should be kept directly in the root folder)


1) gwl_data_scraper.py  -- pip installations required [pip install requests]
	- The first script that should be run to create the data 
	- Downloads all available "GROUND-WATER LEVEL" data for last 3 yrs from dates - 2023-01-01 to 2026-01-01 from india.wris official gov website.
	- CURRENTLY , Downloads Only selective data for Hackathon demo purposes ::
		-- Only 5 States -> Rajasthan , Madhya Pradesh , Maharashtra , Uttar Pradesh , Gujarat [TOP 5 INDIA's largest States]
		-- Only 1 well per district for all available districts [1 well -> well which has most consistent data in the 3 yr window]
	- Saves data automatically in 5 Folders at root level with folder_name as state name , and file name as district_name.csv
	- contains inconsistent data and some missing timestamps due to sensor faults
	- Also contains those districts that have very less data (<5 rows) which means manual mode of acquisition of data and no DWLRs present.





2) sort_asceding_dt.py
	- The data from india-wris is not only inconsistent but also not in a ascending order based on datetime due to pagination.
	- This python scripts corrects it by first accessign all 5 state-folders one-by-one and ascending the csv files and resaving them without changing anything else.






3) add_seasonal_features.py
	- This is the final script that prepares our primal dataset for predicting future groundwater levels.
	- Initially , our plan was to use ARIMA , which is very good in predicting time-series data , which is future water-level data based on past data.
	- But after research we decided to switch to -> "ARIMAX" , which stands for , ARIMA + eXogenous Variables , now we can include seasonal changes like "baarish ke time gw increase hona" , "summer ke time speedily deplete hona" , using the exogenous variables like sin_month and cos_month , we can connect dec->jan [by using sin and code otherwise , 0 is far from 12 , but sin0 is not that far from sin12]
	- So , what this script does is ki , fetches all distrcits in all state-folders , and adds 3 more columns[features] that improve the accuracy of ARIMA by far , because now ARIMA doesn't treat the data as a single baseline , but with seasonal curvs and ups&downs.
	- Now , after running this file our first dataset is ready , which is district.csv for all districts in all states.

	- Now we will move on to generating the next dataset which has many meaningful data and uses "RANDOM FOREST" to predict the recharge pattern of groundwater level instead of just time-series forecasting.





4) rain_data_scraper.py 
	- Second script , after gwl data is fully downloaded.
	- Downloads Rainfall level corrected (mm/day) & Temperature at 2 Metres (Degree Celsius) from NASA's official API
	- reads lat/long from all district.csv files and downloads rainfall and temp data for that particular lat/long for same 3 yrs period (2023-01-01 to 2026-01-01)
	- Saves data in district_rain.csv
	- Contains consistent data for full 3 yrs period from NASA's Official API





5) data_extractor.py
	- This is a utility script , that divides data into 4 new CSV's ::
		-- Extracts those districts that have less than 5 rows data , indicating manual mode of acquisition and no DWLRs present or Faulty or Inactive Sensors , and saves those districts into "inactive_districts.csv"
		-- Extracts those districts that have no ground-water level record for the given 3 year window and saves those district names in "no_station_districts.csv"

	- After saving districts that cannot be trained under AI due to lack of data present , it now creates 2 more CSV'S ::
		-- First it creates the "soil_mapping.csv" , which has all districts mapped to their respective soil types , this data is mapped based on OFFICIAL ICAR CHARTS AND DATA , by myself and not by any API.
		-- Then it creates the "urban_mapping.csv" , which has all districts mapped to their urban or rural occurrence [1 or 0] , based on their population density , if their population_density > 500 people/sq.km , they are marked as urban[1] . The population_density data is taken from the official sources of the 2011 Census data , and the ">500" wala is regarded as the most common threshold in India to divide between grown-up Urban cities and rural cities.





6) build_recharge_dataset,py
	- This is the main script that creates a single .CSV from multiple csv files we had created till now.
	- This CSV file generated after this stage will be cleaned once and then used as single training dataset for " Predicting water-level recharge trends "  by using "RANDOM FOREST" as its model-type.
	- This file combines the district_rain.csv's and the soil_mapping.csv and urban_mapping.csv into one single file named "recharge_training.csv".
	- This csv contains all imp features required to understand and predict recharge trends for all districts at once.
	- Features : 
		-- district [district name]
		-- state [state name]
		-- year 
		-- month
		-- rain_total [total rain in that whole month , derived from district_rain.csv]
		-- rain_avg [avg rain in that month , derived by , rain_total/30]
		-- temp_avg [avg temp throughout the month , derived from district_rain.csv]
		-- soil [derived from soil_mapping.csv for that particular district , the mapping keys are :: {{alluvial = 1,black = 2,red = 3,sandy = 4,laterite = 5}}
		-- urban [derived from urban_mapping.csv for that particular_district , the mapping keys are :: {{1 = urban, 2 =  rural}} , This feature is included to give more accuracy and understanding , since rural areas are observed to have better recharge patterns then urban areas.
		-- well_depth [derived from district.csv]
		-- acquifier type [derived from district.csv] the mapping keys are :: {{"Unconfined":1,"Semi-Confined":2,"Confined":3}}, This feature was included because , the official wris site quotes - Different acquifier tend to have different recharge rates.
		-- gw_delta [The main target variable , indicates depletion or recharge trend and speed , negative value represents depletion [higher neg value = more faster depletion] and positive value represents rechargs [ higher pos value = more faster refill]





7) clean_recharge_dataset.py
	- This python file is the last script in the order , all it does is clean the "recharge_training.csv" file and finds any na rows due to inconsistent or fault DWLR data , and compensates for them by deleting rows it not important , or filling na's by median or mode data as required.
	- After cleaning , this script gives us the final cleaned training dataset which we can use to train in orange or as preferred.





8) add_lag_features.py
	- This is the last-scond step before training our final dataset , adding lag features .
	- this may not seem a important step , but believe me , this is a very very crucial step if u want your model to be accurate enough , not just some proof-of-concept BS
	- this file adds 5 lag features to the cleaned_dataset and saves it into "recharge_rf_ready.csv"
	- Lag features are nothing but simple memory features , gw_delta_lag1 contains last month's gw_delta and gw_delta_lag contains second-last months gw_delta and rain_total_lag1 contains last month's rain_total
	- Why we need to save previous months ?? as you could have guessed , to improve model's accuracy and tell it that yes , current ground-water level not only depends on current rain_data but more importantly on last month's rain avg and temp avg and water_level_avg s well.
	- This simple looking , but crucial step helps the model connect the data with last months data and hence improve a lot in the accuracy.





9) fix_recharge_outliers.py
	- We noticed that just cleaning it isn't optimal since there are many such points which are faulty from the wris - wource itself which give very large outliers that can hinder random_forest training and lower its score brutally.
	- So for that , we will first remove all outliers by running this code once and then we will be ready to train our data.