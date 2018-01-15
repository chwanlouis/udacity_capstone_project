# Machine Learning Engineer Nanodegree

## Capstone Proposal
Louis Wan  
13th Jan, 2018

## Proposal

### Domain Background

Financial market is dynamic and full of uncertainty. Lots of financial industry like hedge funds have to works well with data, like time series data like the price of stocks and futures and multidimension data like fundamental factors of a company. Investment bank hire many financial expert to building strategies for trading but people works emotionally. Algorithmic trading can help expert to do judgement but the signals and indicators are all defined by human. Algo-trading just provides a systematic way to trade according to a human logic. Can we build a reinforcement agent that can recognize signal by itself? This is the propose of this project.

### Problem Statement

Over hundreds of technical and statistical indicators are used for machine learning based trading agent. After training, the agent can turn the indicators into trading decisions(buy or sell with different amount)

### Datasets and Inputs

The project will use Sun Life Rainbow mandatory provident fund(MPF) Scheme for finanical trading products. The reason why using Sun Life MPF is because of these funds include different kind of global instrutment such as bonds, stocks and foreign exchanges. Less noise have to tackle with. Secondly, Sun Life MPF service charge is counted and reflected inside the product itself with little entry barrier. Usually, the bond trading is requiring 1.5M cash in security account which is not feasible for majority of people. The twelve funds are provided by Sun Life MPF.

Sun Life Rainbow MPF Scheme 

#### included for trading
1. Sun Life MPF Conservative Fund (Class B), Launch Date: 01 Dec 2000
2. Sun Life MPF Hong Kong Dollar Bond Fund (Class B), Launch Date: 01 Dec 2000
3. Sun Life MPF Stable Fund (Class B), Launch Date: 01 Dec 2000
4. Sun Life MPF Balanced Fund (Class B), Launch Date: 01 Dec 2000
5. Sun Life MPF Growth Fund (Class B), Launch Date: 01 Dec 2000
6. Sun Life MPF Global Equity Fund (Class B), Launch Date: 01 Mar 2008
7. Sun Life MPF Asian Equity Fund (Class B), Launch Date: 01 Mar 2008
8. Sun Life MPF Hong Kong Equity Fund (Class B), Launch Date: 01 Dec 2000
9. Sun Life MPF Greater China Equity Fund (Class B), Launch Date: 01 Mar 2008

#### excluded from trading
10. Sun Life MPF Global Bond Fund (Class B), Launch Date: 01 Jan 2010
11. Sun Life MPF RMB and HKD Fund (Class B), Launch Date: 30 Jun 2012
12. Sun Life FTSE MPF Hong Kong Index Fund (Class B), Launch Date: 10 Dec 2013

Fund number 1 to 9 will be used for trading only due to the length of data of fund No. 10 to 12 is not enough. For technical indicators, I will use the python package named TA-lib for generating indicators. Since the only close price of fund can be used, some of the indicators will not be available for use.

### Solution Statement
_(approx. 1 paragraph)_

'''
In this section, clearly describe a solution to the problem. The solution should be applicable to the project domain and appropriate for the dataset(s) or input(s) given. Additionally, describe the solution thoroughly such that it is clear that the solution is quantifiable (the solution can be expressed in mathematical or logical terms) , measurable (the solution can be measured by some metric and clearly observed), and replicable (the solution can be reproduced and occurs more than once).
'''

![alt text](https://github.com/chwanlouis/udacity_capstone_project/blob/master/md_figure/fig_1.png "Figure 1")

### Benchmark Model
_(approximately 1-2 paragraphs)_

'''
In this section, provide the details for a benchmark model or result that relates to the domain, problem statement, and intended solution. Ideally, the benchmark model or result contextualizes existing methods or known information in the domain and problem given, which could then be objectively compared to the solution. Describe how the benchmark model or result is measurable (can be measured by some metric and clearly observed) with thorough detail.
'''

### Evaluation Metrics
_(approx. 1-2 paragraphs)_

'''
In this section, propose at least one evaluation metric that can be used to quantify the performance of both the benchmark model and the solution model. The evaluation metric(s) you propose should be appropriate given the context of the data, the problem statement, and the intended solution. Describe how the evaluation metric(s) are derived and provide an example of their mathematical representations (if applicable). Complex evaluation metrics should be clearly defined and quantifiable (can be expressed in mathematical or logical terms).
'''

### Project Design
_(approx. 1 page)_

'''
In this final section, summarize a theoretical workflow for approaching a solution given the problem. Provide thorough discussion for what strategies you may consider employing, what analysis of the data might be required before being used, or which algorithms will be considered for your implementation. The workflow and discussion that you provide should align with the qualities of the previous sections. Additionally, you are encouraged to include small visualizations, pseudocode, or diagrams to aid in describing the project design, but it is not required. The discussion should clearly outline your intended workflow of the capstone project.
'''

-----------

**Before submitting your proposal, ask yourself. . .**

- Does the proposal you have written follow a well-organized structure similar to that of the project template?
- Is each section (particularly **Solution Statement** and **Project Design**) written in a clear, concise and specific fashion? Are there any ambiguous terms or phrases that need clarification?
- Would the intended audience of your project be able to understand your proposal?
- Have you properly proofread your proposal to assure there are minimal grammatical and spelling mistakes?
- Are all the resources used for this project correctly cited and referenced?
