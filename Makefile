all:
    ./gsl.py $1 --stdout | java -jar ../ssm/ssm.jar --stdin

compile:


link: