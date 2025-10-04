from functions import main
import os

print("USER:", os.environ.get("RABBITMQ_USER"))
print("PASS:", os.environ.get("RABBITMQ_PASS"))

if __name__ == "__main__":
    main()
