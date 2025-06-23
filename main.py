from data_loader import get_resources
from create_model import create_model
import time

def main():
    start_time = time.time()
    data = get_resources()  # Reading the data from Excel

    # Create the optimization model and call all necessary functions to define variables, constraints, and the objective function
    m = create_model(data,include_flow=True, penalize=True)

    end_time = time.time() # End of execution timer
    execution_time = end_time - start_time
    print(f"\nTotal execution time: {execution_time:.2f} seconds")

if __name__ == "__main__":



    main()
