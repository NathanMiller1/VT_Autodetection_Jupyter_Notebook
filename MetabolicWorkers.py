import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error

class MetabolicTest:
    def __init__(self, file_path, which_vt):               
        self.file_path = file_path
        
        # Load Headers and Data
        all_headers = pd.read_excel(self.file_path, header=0, nrows=0).columns.tolist()
        data_df = pd.read_excel(self.file_path, skiprows=2, names=all_headers)

        # Extract and Rename Columns
        target_cols = ["Time", "t", "Rf", "Ve", "VE", "VO2", "VCO2", "RQ", "VE/VO2", "VE/VCO2", "HR", "Phase", "PetO2", "PetCO2", "Fat"]
        available_cols = [c for c in target_cols if c in data_df.columns]            
        self.raw_df = data_df[available_cols].copy()

        variable_dict = {'RQ': 'RER', 't': 'Time', 'VE': 'Ve'}
        for k, v in variable_dict.items():
            if k in self.raw_df.columns:
                self.raw_df.rename(columns={k: v}, inplace=True)
        
        # Remove any extra rows
        self.raw_df = self.raw_df.dropna(subset=['Time']).reset_index(drop=True)

        # Convert VO2 and VCO2 to L/min
        if 'VO2' in self.raw_df.columns:
            self.raw_df['VO2'] = self.raw_df['VO2'] / 1000
        if 'VCO2' in self.raw_df.columns:
            self.raw_df['VCO2'] = self.raw_df['VCO2'] / 1000
            
        # Filter for Exercise Phase
        if 'Phase' in self.raw_df.columns:
            self.raw_df = self.raw_df[self.raw_df['Phase'].astype(str).str.contains('Exercise', case=False, na=False)].copy()
        
        # Sort by VO2
        self.raw_df = self.raw_df.sort_values(by="VO2", ascending=True).reset_index(drop=True)

        # Trim by RER
        if 'RER' in self.raw_df.columns:
            min_rer_idx = self.raw_df['RER'].idxmin()
            self.raw_df = self.raw_df.loc[min_rer_idx:].reset_index(drop=True)
            if which_vt == 'vt1':
                self.raw_df = self.raw_df[self.raw_df['RER'] <= 1.05].reset_index(drop=True)
        
        # Calculate excess CO2 and excess VE
        self.raw_df['excess_co2'] = self.raw_df["VCO2"]**2 / (self.raw_df["VO2"] + 1e-8) - self.raw_df["VCO2"]
        self.raw_df['excess_Ve'] = self.raw_df["Ve"]**2 / (self.raw_df["VCO2"] + 1e-8) - self.raw_df["Ve"]

    def _normalize_errors(self, results):
        s = pd.Series(results).replace(-1.0, np.nan)
        e_min, e_max = s.min(), s.max()
        s = s.fillna(e_max)
        if e_max > e_min:
            return ((s - e_min) / (e_max - e_min)).tolist()
            
        return [0.0] * len(results)

    def _segmented_regression(self, x_name, y_name):
        x = self.raw_df[x_name].values.reshape(-1, 1)
        y = self.raw_df[y_name].values.reshape(-1, 1)
        
        results = []
        for i in range(len(x)):
            time_val = str(self.raw_df['Time'].iloc[i]).split(' ')[-1].split('.')[0]
            vo2_val = self.raw_df['VO2'].iloc[i]
            vco2_val = self.raw_df['VCO2'].iloc[i]

            if (i < 4) or (i > len(x) - 5):
                results.append({'Time': time_val, 'error': -1.0, 'VO2': vo2_val, 'VCO2': vco2_val})
                continue
                
            # Split data into two groups
            x1, y1 = x[:i], y[:i]
            x2, y2 = x[i:], y[i:]
            
            # Fit lines
            model1 = LinearRegression().fit(x1, y1)
            model2 = LinearRegression().fit(x2, y2)
            error = mean_squared_error(y1, model1.predict(x1)) + mean_squared_error(y2, model2.predict(x2))
            results.append({'Time': time_val, 'error': error, 'VO2': vo2_val, 'VCO2': vco2_val})
        
        res_df = pd.DataFrame(results)
        res_df['error'] = self._normalize_errors(res_df['error'].values)
        
        return res_df

    def _detect_vt1_vslope_1986(self):
        vo2 = self.raw_df['VO2'].values.reshape(-1, 1)
        vco2 = self.raw_df['VCO2'].values.reshape(-1, 1)
        
        # Fit single regression line through all data
        global_regr = LinearRegression().fit(vo2, vco2)
        global_regr_vco2 = global_regr.predict(vo2)
        m_global = global_regr.coef_[0][0]
        b_global = global_regr.intercept_[0]
    
        # Fit regression lines above and below all possible threshold points
        results = []
        for i in range(len(vco2)):
            time_val = str(self.raw_df['Time'].iloc[i]).split(' ')[-1].split('.')[0]
            if (i < 4) or (i > len(vco2) - 5) or vco2[i] > global_regr_vco2[i]:
                results.append({'Time': time_val, 'error': -1.0, 'VO2': vo2[i][0], 'VCO2': vco2[i][0]})
                continue
            
            # Get VO2 & VCO2 above and below the threshold point
            vo2_below  = vo2[:i]
            vco2_below = vco2[:i]
            vo2_above  = vo2[i:] 
            vco2_above = vco2[i:]

            # Fit regression lines above and below threshold point
            regr_below = LinearRegression().fit(vo2_below, vco2_below)
            regr_above = LinearRegression().fit(vo2_above, vco2_above)
            
            # Line equation: y = m*x + b
            m_below = regr_below.coef_[0][0]
            b_below = regr_below.intercept_[0]
            m_above = regr_above.coef_[0][0]
            b_above = regr_above.intercept_[0]
            
            # Upper regression line must be steeper than the lower regression line by >0.1
            if (m_above - m_below) <= 0.1:
                results.append({'Time': time_val, 'error': -1.0, 'VO2': vo2[i][0], 'VCO2': vco2[i][0]})
                continue
            
            # Find intersection of the lower and upper regression lines
            vo2_int = (b_above - b_below) / (m_below - m_above)
            vco2_int = m_below * vo2_int + b_below
            
            # Find distance from intersection of lower/upper regression lines to the global regression line
            distance = abs(m_global * vo2_int - vco2_int + b_global) / np.sqrt(m_global**2 + 1)
            
            # Calculate RMSE for lower and upper regression lines
            rmse_below = np.sqrt(mean_squared_error(vco2_below, regr_below.predict(vo2_below)))
            rmse_above = np.sqrt(mean_squared_error(vco2_above, regr_above.predict(vo2_above)))
            
            # Store the error: distance / sum of RMSE
            final_error = distance / (rmse_below + rmse_above + 1e-8)
            results.append({'Time': time_val, 'error': final_error, 'VO2': vo2[i][0], 'VCO2': vco2[i][0]})
        
        res_df = pd.DataFrame(results)
        res_df['error'] = self._normalize_errors(res_df['error'].values)
        
        return res_df

def process_single_task(task_args):
    file_path, config, file_name = task_args
    x_col, y_col, which_vt = config
    tester = MetabolicTest(file_path, which_vt)
    
    if x_col == "V-Slope":
        method_name = "V-Slope"
        res_df = tester._detect_vt1_vslope_1986()
    
    elif x_col == "RQ=":
        method_name = f"RQ={y_col}"
        res_df = tester.raw_df.copy()
        res_df['error'] = tester._normalize_errors((res_df['RER'] - float(y_col)).abs())
    
    elif x_col == "high_rer_mask":
        method_name = f"High_RER_{y_col}_Mask"
        res_df = tester.raw_df.copy()
        res_df['error'] = (res_df['RER'] > float(y_col)).astype(float)
    
    elif x_col == "fat_max_mask":
        method_name = "FatMax_Mask"
        res_df = tester.raw_df.copy()               
        res_df['error'] = (res_df.index <= res_df['Fat'].idxmax()).astype(float)
    
    else:  # Segmented regression
        method_name = f"{y_col}_vs_{x_col}"
        res_df = tester._segmented_regression(x_col, y_col)

    final_results = []
    for _, row in res_df.iterrows():
        final_results.append({
            "FileName": file_name,
            "Method": method_name,
            "Time": row['Time'],
            "VO2": row['VO2'],
            "VCO2": row["VCO2"],
            "Normalized_Error": row['error'],
        })
        
    return final_results
    