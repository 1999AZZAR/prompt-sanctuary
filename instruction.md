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

4. **The .env file:**

   - Rename the `.env.example` file in the `web` folder to `.env`.
   - Fill out the necessary api key.
   - Save and close the file.
   - You can get your Gemini API key from [here](https://makersuite.google.com/app/apikey) and follow the instructions there.

5. **Run the Application:**

   - Start the Flask application:

     ```bash
     cd web/
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
     cd web/
     python app.py
     ```

     The application will start, and you can access it through the specified port.

## Usage

- **Access:**
  - You can now access it through `http://127.0.0.1:5000` or `http:localhost:5000`.
- **Home Page**: Accessible from the root URL (`/`). This is the starting point of the application.
- **Generate Content**: Navigate to `/generate` to access the content generation page. You can input text or select options to generate content.
- **Advanced Options**: For more advanced content generation, navigate to `/advance` and provide the required parameters.
- **Library**: Access various content generation templates and tools from the library section. Navigate to `/library` and choose the desired option.

Note: Remember to deactivate the virtual environment when you're done:

```bash
# On Windows:
deactivate

# On Unix or MacOS:
deactivate
```
