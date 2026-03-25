# Voyage

Voyage is a dynamic, Django-based learning platform that leverages AI to generate personalized educational content. Instead of pre-recorded courses, Voyage creates custom-tailored "Expeditions" (course-based learning paths for specific topics), complete with lessons, quizzes, and adaptive recommendations based on a user's evolving interests.

## Core Features

- **AI-Powered Learning Expeditions**: Type in any skill you want to learn, and Voyage will generate a structured learning path broken down into sequential Chapters. For each chapter, the platform dynamically generates in-depth, markdown-formatted lessons.
- **Dynamic Quizzes & Knowledge Checks**: After completing lessons, users are tested with AI-generated multiple-choice quizzes. You must pass these quizzes to prove your knowledge before advancing to the next chapter.
- **Adaptive Interest Tracking**: Voyage learns what you like. The platform tracks your engagement across different subjects and calculates an "interest factor", which is then used to suggest new, relevant topics and expeditions.
- **Search & Instant Lessons**: Have a quick question? Search for any topic and Voyage will generate an instant, comprehensive lesson containing an introduction, core concepts, a Q&A section, and further reading links.

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/azh412/voyage.git
   cd voyage
   ```

2. **Install dependencies:**
   Make sure you have Python installed, then install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Environment Variables:**
   Create a `.env` file in the root directory (where `manage.py` is located) or export these variables in your terminal to keep your secrets secure:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   DJANGO_SECRET_KEY=your_django_secret_key_here
   ```
   *(Note: The platform relies heavily on OpenAI's GPT-3.5-turbo model, so a valid API key is required).*

4. **Run Migrations:**
   Initialize the SQLite database with:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Start the Development Server:**
   Launch the app locally:
   ```bash
   python manage.py runserver
   ```
   The application will be accessible at `http://127.0.0.1:8000/`.

## Contributing
Contributions, issues, and feature requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

-azh
