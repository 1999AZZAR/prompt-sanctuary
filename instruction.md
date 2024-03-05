# instruction

## Initial Setup

1. **Clone the Repository:**
   - Open a terminal or command prompt.
   - Run the following commands:

     ```bash
     git clone https://github.com/1999AZZAR/prompt-sanctuary.git
     cd prompt-sanctuary
     ```

2. **Create a Virtual Environment (Optional but recommended):**
   - If you don't have `virtualenv` installed, you can install it using:

     ```bash
     pip install virtualenv
     ```

   - Create a virtual environment in the project folder:

     ```bash
     python -m venv myvenv
     ```

   - Activate the virtual environment:
     - On Windows:

       ```bash
       .\myvenv\Scripts\activate
       ```

     - On Unix or MacOS:

       ```bash
       source myvenv/bin/activate
       ```

3. **Install Dependencies:**
   - Install the required dependencies using:

     ```bash
     pip install -r requirements.txt
     ```

4. **Create the .env file:**
    - Create a .env file on the `web` folder
    - write this to that file:

    ```text
    GENAI_API_KEY="Your-api-key"
    ```

    - safe it and close the file.
    - you can get your gemini api key from [here](https://makersuite.google.com/app/apikey) and follow the instruction there.

5. **Run the Application:**
   - Start the Flask application:

     ```bash
     python app.py
     ```

     The application will run on port 2500.

## Subsequent Runs

1. **Activate Virtual Environment (if using venv):**
   - If the virtual environment is not already activated:
     - On Windows:

       ```bash
       .\myvenv\Scripts\activate
       ```

     - On Unix or MacOS:

       ```bash
       source myvenv/bin/activate
       ```

2. **Run the Application:**
   - Start the Flask application:

     ```bash
     python web/app.py
     ```

     The application will start, and you can access it through the specified port.

## Usage

- **access:**
  - now you can access it trough `http://127.0.0.1:5000`.

NB: Remember to deactivate the virtual environment when you're done:

```bash
# On Windows:
deactivate
# On Unix or MacOS:
deactivate
```
