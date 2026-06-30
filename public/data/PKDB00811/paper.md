# Square root law model for the delivery and intestinal absorption of drugs: a case of hydrophilic captopril


## Abstract

The in vivo release and absorption of drugs are dependent on the interplay between many factors related to compound, formulation, and physiological properties. The mathematical models of oral drug absorption attempt to strike a balance between a complete description that takes into consideration as many independent factors as possible, and simple models that operate with fewer parameters, based mainly on critical factors. The latter models are by far more robust and easier to apply to predict the extent and sometimes even the rate of absorption. The present paper attempted to develop a simple model to describe the time course of absorption of the hydrophilic drug captopril (CPT) at the early phases of absorption, with implications mainly in the induction and early stages of achieving its therapeutic effect. As a phenomenological model, the instantaneous release of CPT was considered in the gastrointestinal fluid, leading to a constant drug concentration for a prolonged time, followed by a ‘long path diffusion’ inside the intestinal wall and a very low concentration at the interface intestinal wall-blood. These conditions regarding CPT concentration were translated into initial and boundary mathematical conditions for the diffusion equation in the intestinal wall. The solution of the diffusion equation led in the end to a square root law describing the dependence between the fraction of the drug absorbed and time. The model was successfully applied to data obtained in five bioequivalence studies: three comparing plasma levels achieved after the administration of a single dose of CPT 50 mg, one evaluating CPT pharmacokinetics after a 100 mg dose, and a fifth comparing CPT pharmacokinetics of two fixed-dose combinations of CPT 50 mg and hydrochlorothiazide 25 mg.


## Introduction

Release in the gastrointestinal tract and the intestinal absorption of drugs into the bloodstream are the first steps in the pharmacokinetics of orally administered drugs. The rate and extent of absorption are essential factors in pharmacokinetic-pharmacodynamic coupling (Mager et al.,; Crommelin et al.,), and finally in the balance between therapeutic efficacy and safety of drugs. Research and development of a new drug include answering questions about how the respective drug is released, absorbed, metabolized, distributed, and eliminated.

Factors affecting drug release and absorption can be divided into three different categories. The first category is represented by the structure of the pharmaceutical formulation and a multitude of physicochemical properties of the active compounds, including pKa (Wan and Ulander,; Manallack,), solubility in biorelevant media (Mircioiu et al.,; Preda et al.,), the partition coefficient (Perez et al.,), permeability in different segments of the gastrointestinal (GI) tract (Lozoya-Agullo et al.,; Chung and Kesisoglou,; Vertzoni et al.,), particle size distributions (Hintz and Johnson,), supersaturation (Hens,), the substrate of transporters (González-Alvarez et al.,), the effect of interactions between poorly soluble drugs and surface-active agents (Mircioiu et al.,), etc. However, it is essential to understand that this multitude of parameters is in fact a mathematical space with a smaller number of dimensions, as these parameters are not independent.

Anatomical and physiological conditions represent the second component of the drug-living body interaction. Factors, such as pH, peristalsis (Enobong et al.,), post-dose contractions (Bermejo, et al.,), physiological surfactants (Carmona-Ibanez et al.,), buffer capacity (Hens et al.,), accumulation and transfer of drugs and physiological surfactants at interfaces (Bermejo et al.,), gastric emptying (Chrenova et al.,), and enterohepatic circulation (Tvrdonova et al.,) significantly influence the rate and extent of absorption.

In terms of pharmaceutical technology, the inclusion of drugs in colloidal vectors, i.e. formulation as an immediate or extended-release drug, as well as the addition of surfactants and the formation of supramolecular structures (Miclea et al.,; Suta et al.,) are usual methods for improving bioavailability and to better manage pharmacokinetics. Mathematical models concerning absorption attempt to find a balance between a complete description that takes into consideration as many independent factors as possible, and simple models that operate with fewer parameters, based mainly on critical factors. Models of the first type are very complex and are associated with insurmountable difficulties in finding analytical expressions and the identification of parameters for particular cases. The second type of model leads to simple laws, but performance in fitting experimental data is sometimes reduced. Almost all models proposed until now have attempted to estimate the fraction of dose absorbed (FRA). This includes the pH partition model (Chanker,), absorption potential models (Dressman et al.,; Macheras and Symillides,), film models (Amidon et al.,), and macroscopic balance (Sinko et al.,).

Dynamic models have attempted to predict both the fraction of dose absorbed and the rate of drug absorption and to correlate them to pharmacokinetic models for predicting plasma concentration profiles. Such models are however much too complex, requiring extensive physicochemical and physiological information (Lin and Wong,). There have been numerous attempts considering the factors listed above to be included in mathematical models, but this has led to increasingly cumbersome models, which have been very difficult to apply in practice, and fitting algorithms being generally unstable, i.e. sudden, great changes in the estimated parameters in the case of small changes in the input data.

This paper aimed at a simple model, with an analytical simple solution, restricted to a finite time (Macheras et al.,) to describe the time course of absorption of the CPT, deduced by deconvolution of its plasma levels in five bioequivalence studies.


## Methods


### In vitro release

Release experiments were performed using the USP basket apparatus (ERWEKA DT800 HH model) at a rotation speed of 50 rpm, as specified in the CPT tablet monography of USP32 (USP29-NF24). As a release medium, 900 ml of 0.01 N HCl was used. Samples with a volume of 2 ml were collected at 5, 10, 15, 20, and 30 min and then filtered through a 0.45 µm Teflon® filter.

Dissolution studies were performed in the frame of five different bioequivalence studies. Experiments were run on 12 tablets of each formulation. The quantification of CPT was achieved by using a spectrophotometric method at λ = 205 nm.


### Clinical study

A single dose of CPT was administered to subjects (n > 20) in five, cross-over, two-period, two sequence bioequivalence studies under fasting conditions, with a washout period of 6 days between period I and period II. Studies were approved by the Romanian National Ethics Committee and the Romanian National Medicines Agency.

Three studies, denoted as B, M, and L, compared plasma levels achieved after the administration of CPT (CPT) 50 mg. Another study, denoted S, compared the pharmacokinetics of CPT after a 100 mg dose. Because it is common to combine CPT with hydrochlorothiazide (HCT) in a single tablet, the fifth study compared two formulations containing a fixed-dose combination of 50 mg CPT and 25 mg HCT to test the effect of the pharmacokinetic interaction on CPT absorption.

Blood samples were collected before, and 0.5, 1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10, 12, and 24 h after drug administration. Plasma levels of the active substance CPT were determined using a validated liquid chromatographic method (Medvedovici et al.,). Pharmacokinetic analysis of the active components was performed using non-compartmental methods and modeled using mono- and bicompartmental models. The estimation of the parameters of the compartmental models was performed using Pk Solver 2 software version 2.2.


### Calculation of the time dependence of the absorption fraction

The absorption fraction FRA(t) of CPT was deduced from its plasma levels. It was observed that, after the time of maximum concentration, plasma levels decreased in two consecutive monoexponential phases: one from the maximum concentration to 4 h and a second, slower release phase at the tail of the curve, corresponding to <5% of the area under the curve (Figure 1).


> **Figure.** Concentration and logarithm of concentration as a function of time (study B, reference drug) after the time point of the maximum concentration.

The slope of the first regression line was considered as ‘distribution constant’ and the second slope as an elimination constant, although their interpretation is more complex.

In a mass balance approach, similar to the Nelson Wagner method, it was considered that the absorbed quantity at time t is the sum of the quantity in the blood at moment t and the quantity that has disappeared from the blood via first-order kinetics, with a rate constant kd  where Vd is the distribution volume,  is the area under the concentration-time curve of the drug from time 0 to time ti calculated from experimental data using the trapezoidal rule, and  is the area under the concentration-time curve of the drug from time 0 to infinity.


## The square root model of absorption from an infinite reservoir

The model supposes diffusion-controlled absorption and gives a solution for the equation   where c(x,t) is the concentration in the epithelial wall and D is the diffusion coefficient, in the following phenomenological conditions, translated into initial and boundary conditions (Table 1).


**Mathematical initial and boundary conditions and solution of the diffusion equation.**


```
Intestinal fluid	Intestinal wall	Blood	 	Phenomenological condition	Phenomenological conditions	Phenomenological conditions	 	Instant release of CPT in intestinal fluid and set up of a constant concentration for a significant time interval.	Concentration of CPT in the intestinal wall at the interface with intestinal fluid is initially zeroConcentration increases suddenly and remains constant at a value Diffusion of CPT in the wall is a ‘long path process’ such that at the interface of intestinal wall with the blood the concentration is very low and we can consider it zero	The blood is a ‘compartment,’ with same concentration at all points	 	Mathematical condition	Mathematical, initial and boundary conditions	Mathematical conditions	 	c(x,t) = constant	The solution of the equation is:	c(x,t) = c(t)	 	 		 	 	 	Flux: Transferred amount Q(t)
```

1. Since the drug is hydrophilic, its release in vivo is supposed to be very rapid, similar to release in vitro. Intestinal fluid is considered as a compartment, which means a spatial homogeneous concentration. Since permeability is low, the intestinal wall act as a barrier to transport so that the concentration remains high and relatively constant for a significant time. Under these conditions, intestinal fluid can be considered mathematically as an infinite reservoir with a constant concentration – c0, similar to a thermostat in heat transfer theory. This corresponds to the boundary condition for the diffusion equation:

2. If we suppose that the active substance is not present in the intestinal wall before absorption, the mathematical ‘initial condition’ for the differential equation of diffusion is:

3. The diffusion domain is considered the intestinal wall.

4. Considering the thickness of the intestinal wall as a long pathway for diffusion, it is possible to consider mathematically diffusion in a semi-infinite medium with the condition at the infinite frontier:

The solution of the diffusion equation for the concentration inside the intestinal wall with these initial and boundary conditions can be obtained by its transformation in an ordinary linear equation after application of the Laplace transform to c(x,t) as a function of t. Solving the obtained differential equation and applying the inverse Laplace transform gives (see Appendix A) the solution:  where erf is the ‘error function’:

The main problem proposed in this model is to calculate the kinetics of transfer across the internal face of the intestinal wall, more exactly the quantity of the active component released from the intestinal fluid as a function of time. Emphasis is placed on the rate of transfer, FRA(t). For this aim, let us calculate the flux J(t) (quantity transferred in a time unit dm/dt across an area A) of the drug across the intestine face of the intestinal wall (x = 0).

We applied Fick’s first law:

If we denote the combined variable  by y, then the flux J will be:

It was therefore found that the flux of the drug across the interface is proportional to the inverse of the square root of time. We can further compute the quantity Q(t) of drug transferred after time t, across the interface x = 0:

The result indicates that the quantity of active substances which left the intestinal content and can be considered as having entered the bloodstream is a linear function of the square root of time. Hence, if the representation of the absorbed fraction as a function of the square root of time is a straight line, we indicate that the model is applicable.


## Results


### In vitro release and pharmacokinetics

In vitro release was very rapid from all 10 formulations. Two tested formulations had a somewhat slower release, but at 20 min, the release was more than 80% complete, regardless of the formulation (Figure 2(a)). A possible square root law for in vitro release appeared in the case of the two formulations with the slower release.


> **Figure.** Dissolution profiles for the CPT formulations in the B, M, L, and S studies (a) and plasma CPT levels in the evaluated pharmacokinetic studies (b); R: reference drug; T: tested drug.

Following this result, it was reasonable to think that, at least for a period of time, the concentration of CPT in the intestine is high and constant.

Pharmacokinetic was similar for all tested formulations (Figure 2(b)). The two higher mean maximum concentrations corresponded to the double dose (100 mg) and the two somewhat lower concentrations concerned the CPT + hydrochlorothiazide tablets. Pharmacokinetics were proportional to the administered dose, the maximum concentration, and the area under the curve, increasing by approximately double in the case of the 100 mg dose in comparison to the 50 mg dose. Absorption and elimination were very rapid, and the area under the curve at 4 h (AUC0–4 h) was more than 95% of the total area extrapolated to infinity.

Fitting of plasma levels for the 0–4 h time interval led to similar results for both the bicompartmental and monocompartmental models. An improvement occurred in the two-compartment model in the elimination phase, as illustrated for the reference drug in study B in Figure 3, but the improvement after increasing the number of parameters was not statistically significant and refers to the last two points, which correspond to <1% of the area under the curve (Prasacu et al.,; Sandulovici et al.,).


> **Figure.** Monocompartmental (a) and bicompartmental (b) modeling of CPT pharmacokinetics, formulation B.

The calculated elimination constant differed for the two models. The constant that resulted from the monocompartmental model was close to the ‘distribution constant’ calculated from analysis of the regression line fitting the data on the tail of the plasma level curve, as presented above. In fact, a second compartment, following the hydrophilicity of CPT is not the lipid compartment, but rather disulfide conjugation products (Savu et al.,). The final elimination constant associated with small amounts of residual CPT could be connected with the partial reversibility of conjugation reactions.


### Square root modeling of FRA(t)

The method for calculating FRA curves as a function of time is presented in Figure 4. In all cases, a small lag time of ∼5 min appeared, so the zero point was not considered.


> **Figure.** Selection of the domain of estimation of FRA as a linear regression with the square root of time: FRA as function of time (a), FRA as function of square root of time (b).

A saturation of the FRA(t) curve appeared as a rule after reaching the value of 0.8. The square root model was considered for FRA from the first measuring point to the observed saturation of absorption, as a rule around 0.8, since it was considered that the phenomenological and mathematical hypotheses are less valid for greater values, although in several cases the model worked even after this threshold, the entire process being diffusion controlled. This is less usual but not a singular case (Gusea,). A threshold of 0.7 was established based on experience from the last 50 years, in the case of the Higuchi square root law describing the release of active components from solid and semisolid formulations as well as release from almost all supramolecular systems. It was suggested that, in fact, many applications of the square root release law are not connected with the Higuchi model, but rather with release from an infinite reservoir into a semi-infinite medium .

In the fittings, a time lag of ∼5 min was considered. Since in all studies the formulations proved to be bioequivalent, the calculated absorption fractions were analyzed and fitted with the square root of time in parallel. The results of fitting the data to the theoretical model for studies B, L, S, and CPT + HCT are presented in Figure 5.


> **Figure.** Correlation between FRA and square root of time, in studies B (a), L (b), S (c), and CPT + HCT (d); R: reference drug; T: tested drug.

The best results were obtained in study L for both the reference and tested drug, as the correlation was very good (correlation coefficients above 0.99). The slopes of the linear regression were the same for both formulations. In study B, the correlations were good enough and reached values in the neighborhood of FRA = 0.9. The slopes corresponding to the two formulations were slightly different (1.20 and 1.31).

In study S, with double the dose of CPT, the results were not as good as in the case with lower doses. It was noteworthy that the correlation reached a fraction >0.8. In study M (data not shown), the results were very similar to those of study B. The evaluation of joint data on the reference and tested drugs did not significantly change the results.

Some of the differences between pharmacokinetic experiments could arise from differences in the formulation and differences in the characteristics of the healthy volunteers (Mircioiu et al.,). Since the reference drug was the same in all experiments, to estimate the effect of the differences between lots, we represented the FRA and its dependence on the square root of time in the case of the reference formulation in the different bioequivalence studies. As can be seen in Figure 6, the regression lines were approximately parallel, so the influence of the demographic characteristics of the subjects is not a critical factor.


> **Figure.** Correlation between FRA and square root of time for the reference formulation in four different studies within the first hour (a) and for the first 45 min (b).

Last but not least, the performance of the model was also dependent on the time interval of the pharmacokinetic data. As presented above, the first square root time approximated reliable was 0.5, i.e. 15 min. In all cases, apparent saturation appeared after 1 h. Since the time of maximum concentration was 40 min, the fitting performance was also checked in this time interval. As can be seen in Figure 5, restriction to Tmax led to a practically perfect fit.


## Discussion

Almost all mathematical models attempt to predict the fraction of drug absorbed (FRA) as a function of different parameters. Our model tries to predict both FRA and its kinetics, starting from drug concentration in the intestinal wall as a function of both time and space.

The first models of this type, describing the diffusion of drugs in space and time, were inspired by models of heat transfer. Simultaneous longitudinal flow and diffusion in the intestine to the place of absorption was proposed 40 years ago in a classical paper (Ni et al.,), which considered release from an infinite drug reservoir along the intestine, taken as a hollow cylinder. The model solved the diffusion equation under particular initial and boundary conditions, obtaining an analytical solution for c(x,t) which allowed the prediction of the ‘kinetics of appearance of the unabsorbed drug at the end of the intestinal segment.’

Also, an analytical solution was obtained later, ‘assuming that the stomach can be considered as an infinite reservoir with a constant output rate with respect to concentration and volume’ (Yu,). These authors solved the diffusion equation using similar initial and boundary conditions to those used in our paper, using the Laplace transform method, based on the theory of heat transfer (Carslaw and Jaeger,). In fact, this was simpler than the contour integral method used previously and represents a generalization of the Fourier, Laplace, and Fick models from 200 years ago.

It is worth noting the significant fact that, in our model, the space of diffusion is the intestinal wall, not the stomach or the intestine. Other authors have also considered passive membrane diffusion processes, where molecules pass across membranes driven by concentration gradients in the absorption of many drugs (Lennernäs,; Sugano et al.,). Other models are considered ‘dynamic,’ in the sense of considering both the time and space dependence of the concentration in a given domain. The mixing tank model has been developed and utilized to simulate oral absorption phenomena. This approach considers the gastrointestinal tract as one or more serial mixing tanks with linear transfer kinetics. Each tank is considered well-mixed and having a uniform concentration (Dressman et al.,; Dressman and Fleisher,). In the compartmental absorption and transit model (CAT) (Yu,), the process of the passing of drugs through the small intestine was viewed as flow through a series of segments. Each segment was described as a single compartment with linear transfer kinetics. The ACAT model (Agoram,) was developed based on the CAT model to include first-pass metabolism and colon absorption.

If we consider x as a discrete variable taking values from 1 to 7, we can speak about a c(x,t) concentration in the above models, but the interpretation is forced and the diffusion equation is lost. However, consideration of intestinal fluid as a compartment with a rapidly obtained homogeneous concentration is an implicit hypothesis of all pharmacokinetic models for the immediate release of oral dosage forms. A consequence of this hypothesis, in conjunction with the hypothesis of intercompartmental linear transfer in concentration leads to the exponential absorption model, which remains the simplest and most largely accepted model.

In the case of the ingestion of food during drug in vivo dissolution, a critical factor in the determination of the drug concentration in the intestinal fluid is gastric emptying and intestinal peristalsis (Oberle and Amidon,). The hypothesis of a constant reservoir in the intestine ceases to be valid after a certain time as the concentration decreases due to absorption. However, since the absorption of hydrophilic drugs is poor, this remains for a relevant time, approximately constant.

The square root law is not unusual in biopharmacy. It was used to assess the transfer of toxins through the skin (Mircioiu et al.,) and in the case of release from cubosomes as a reservoir (Paolino et al.,). The law is similar to the Higuchi law concerning release from solid and semisolid drug formulations, but it was deduced under very different conditions. In the case of CPT, it seems that the hypothesis is valid. On the other hand, the quantity of CPT distributed in a hypothetical deep compartment is neglected in our model. The model for CPT pharmacokinetics, as other authors have reported before, appears to be a bicompartmental one (Pereira et al.,).

Critical phenomena associated with bile salts after food intake can significantly influence the interfacial transfers of active substances (Pahomi et al.,) and particularly transfer from intestinal fluid to the intestinal wall. Accordingly, the model parameters could be correlated with temporal modifications in the composition of the intestinal fluid.

Finally, many influences could occur due to numerous factors interfering with the initial and boundary conditions considered by the model. Despite these complications, in the case of all five bioequivalence studies of CPT analyzed in this paper, the law worked acceptably well.

A complete presentation of the method of solving differential equations of diffusion, presented in the Appendix, provides evidence of the essential role of the initial and boundary conditions coming from phenomenological conditions. The importance of understanding this correspondence is the prevention of attempts to apply models under conditions incompatible with the conditions of deriving the respective models; this mistake is frequently seen in the analysis of release from all supramolecular systems.


## Conclusions

Consideration of the absorption of an active drug component as diffusion from the intestine as an infinite reservoir in the intestinal wall as a semi-infinite medium led to a square root law for the dependence of the absorbed fraction on time.

A mass balance model for the amount of drug in the blood led to a formula for the calculation of the absorbed fraction starting from plasma level data, similar to that of Nelson-Wagner but based on the distribution constant instead of the elimination constant.

The square root law proved to be applicable in the case of ten different pharmacokinetic experiments concerning CPT 50 and 100 mg and two regarding CPT plus hydrochlorothiazide for ∼80% absorption of the available drug.

Prediction of first, the major part of absorption, is considered significant in the context of prediction of induction and the first part of the effect.


## Author contributions

Constantin Mircioiu performed the mathematical analysis. Victor Voicu analyzed the correspondence between mathematical and physiological conditions. Valentina Anuta and Ion Mircioiu developed and validated the bioanalytical method and performed the analytical assays. Roxana Sandulovici applied the statistical and informatics criteria for the evaluation of the performance of fitting of data by the squared root law. All the authors checked and approved the final draft before submission.


## Disclosure statement

The authors declare that the research was conducted in the absence of any commercial or financial relationships that could be construed as a potential conflict of interest.