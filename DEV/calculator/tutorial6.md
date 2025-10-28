# Question 1

The coverage achieved by our tests was 76%. Considering the theoritical component of Software Engineering, the unit tests shoud coverage around 70% of the code. Since we got 76%, we consider that it is enough.

# Question 2

In the first few times, the code (calulator.py) does not followed PEP8 guidelines, since we got some extra spaces at the end of some code lines and we had only one blank line before "def main()" and PEP8 guidelines expect tow blank spaces. After correcting all these "problems", the pipeline passed.

# Question 3

At the first time, the average complexity of the code was B rank. Since we had the minimum acceptance of A rank, the pipeline job produced a warning containing this information (not passed). Correcting the gitlab-ci pipeline that garantees the minimum of B rank acceptance, we ensure that the pipeline passes.

# Question 4

No vulnerability was found while running the security stage. The pipeline passed at first attempt.