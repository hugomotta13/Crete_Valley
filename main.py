from data_loader import get_resources
from create_model import create_model

def main():
    data = get_resources()  # Reading the data from Excel

    # Create the optimization model and call all necessary functions to define variables, constraints, and the objective function
    m = create_model(data)




if __name__ == "__main__":



    main()
