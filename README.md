# CPET Data Processing & Bayesian Ensemble Framework
This Jupyter notebook (`get_data_multi_process.ipynb`) provides a pipeline for the automated detection of Ventilatory Thresholds (VT1 and VT2) from Cardiopulmonary Exercise Test (CPET) data. It leverages a weighted product of experts model with smoothing and temperature control to synthesize multiple physiological indicators into a unified probabilistic estimate.

## Notebook Sections

### 1. Batch Multi-Process Data Acquisition
Implements a data loading pipeline utilizing `multiprocessing`. This section handles:
* **Scans a directory for CPET Excel files**
* **Parallel Processing** 

### 2. & 3. Single Method Error Calculations and Average MSE Ensemble
These sections calculate residuals for the following VT1 indicators:
* **V-Slope (Beaver 1986)**
* **VCO2 vs. VO2**
* **VE/VO2 vs. VO2**
* **PetO2 vs. VO2**
* **Excess CO2**
* **FatMax Mask**
* **RER Mask**

### 4. VT2 Estimates
This section calculate residuals for the following VT2 indicators:
* **VE/VCO2 vs. VO2**
* **PetCO2 vs. VO2**

### 5. Weighted Product of Experts Ensemble
Instead of a simple average, this section treats each VT1 estimation method as an "expert" and combines their "opinions" into a single probability distribution.

#### Key Features:
* **Softmax with Temperature ($T$): Controls the "sharpness" of the distribution. A lower temperature favors consensus and results in more peaked distributions, while higher temperatures allow for more uncertainty.Signal 
* **Signal Smoothing: Implements Gaussian and Rolling-Window kernels for both individual expert errors and the final combined posterior to reduce high-frequency noise.
* **Product of Experts (PoE) Logic: Log-probabilities are summed (equivalent to multiplying probabilities), ensuring that if one highly-weighted expert identifies a region as "impossible" (zero probability), it is excluded from the final consensus.

#### Statistical Outputs:
* **Maximum A Posteriori (MAP):** The VO2 at the peak of the distribution.
* **Posterior Mean:** The probability-weighted centroid of the distribution, providing a stable estimate in bimodal or noisy scenarios.
* **90% Credible Interval:** Derived from the 5th and 95th percentiles of the cumulative distribution function (CDF) to quantify identification uncertainty.

### 6. Result Visualization
Generates visualizations of the metabolic data overlaid with the calculated posterior distributions and identified breakpoints.

## References
* **Murphy, K. P. (2012).** *Machine Learning: A Probabilistic Perspective.*
