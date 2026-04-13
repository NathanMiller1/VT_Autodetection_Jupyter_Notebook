# CPET Data Processing & Bayesian Ensemble Framework
This Jupyter notebook (`get_data_multi_process.ipynb`) provides a pipeline for the automated detection of VT1 and VT2 from Cardiopulmonary Exercise Test (CPET) data. It facilitates batch data acquisition, multi-method error calculation, and identification of thresholds using a simple average ensemble approach and a Bayesian ensemble approach.

## Notebook Sections

### 1. Batch Multi-Process Data Acquisition
Implements a data loading pipeline utilizing `multiprocessing`. This section handles:
* **Scans a directory for CPET Excel files**
* **Parallel Processing** 

### 2. & 3. Single Method Error Calculations and Average Ensemble
These sections calculate residuals for the following VT1 indicators:
* **V-Slope (Beaver 1986)**
* **VCO2 vs. VO2**
* **VE/VO2 vs. VO2**
* **PetO2 vs. VO2**
* **Excess CO2**
* **FatMax Mask**
* **RER Mask**

### 4. VT2 Estimates
These sections calculate residuals for the following VT2 indicators:
* **VE/VCO2 vs. VO2**
* **PetCO2 vs. VO2**

### 5. Bayesian Weighted Ensemble
This section utilizes a **Bayesian ensemble framework** to combine evidence from the (assumed) independent physiological indicators into a single posterior probability distribution.
* **Maximum A Posteriori (MAP):** The VO2 at the peak of the posterior distribution.
* **Posterior Mean:** The probability-weighted centroid of the distribution, offering robustness against skewed or bimodal data.
* **90% Credible Interval:** Derived from the 5th and 95th percentiles of the cumulative distribution function (CDF) to quantify identification uncertainty.

#### Mathematical Foundation
* **Likelihood Transformation (Murphy 8.4.1):** Transforms normalized segmented-regression errors into likelihoods using an exponential energy function: $L(i) = \\exp(-k \\cdot \\text{error}(i))$.
* **Log-Sum-Exp Trick (Murphy 3.5.3):** Ensures numerical stability during exponentiation and normalization. By identifying $B = \\max(b\_c)$, the framework computes $\\exp(b\_c - B)$ to prevent numerical underflow, ensuring a valid denominator for the probability distribution.
* **Product of Experts:** The log-posterior is computed as a weighted sum of log-likelihoods.

### 6. Result Visualization
Generates visualizations of the metabolic data overlaid with the calculated posterior distributions and identified breakpoints.

## References
* **Murphy, K. P. (2012).** *Machine Learning: A Probabilistic Perspective.*
