from data_loader import get_resources
from create_model import create_model

def main():
    data = get_resources()  # Lendo os dados do Excel


    m = create_model(data)




if __name__ == "__main__":



    main()
