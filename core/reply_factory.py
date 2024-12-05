from .constants import BOT_WELCOME_MESSAGE, PYTHON_QUESTION_LIST


def generate_bot_responses(message, session):
    bot_responses = []

    current_question_id = session.get("current_question_id")
    if not current_question_id:
        bot_responses.append(BOT_WELCOME_MESSAGE)
        session["user_answers"] = []
        session["current_question_id"] = 0

    success, error = record_current_answer(
        message, current_question_id, session)

    if not success:
        return [error]

    next_question, next_question_id = get_next_question(current_question_id)

    if next_question:
        bot_responses.append(next_question)
    else:
        final_response = generate_final_response(session)
        bot_responses.append(final_response)

    session["current_question_id"] = next_question_id
    session.save()

    return bot_responses


def record_current_answer(answer, current_question_id, session):
    '''
    Validates and stores the answer for the current question to django session.
    '''
    # Skip validation for the welcome message (first iteration)
    if current_question_id is None or current_question_id == 0:
        return True, ""

    # Retrieve user answers list from session
    user_answers = session.get("user_answers", [])

    # Validate the answer against the current question's options
    current_question = PYTHON_QUESTION_LIST[current_question_id - 1]

    # Check if the answer is one of the available options
    if answer not in current_question["options"]:
        return False, f"Invalid answer. Please choose from the given options: {', '.join(current_question['options'])}"

    # Store the answer
    user_answers.append({
        "question_id": current_question_id,
        "user_answer": answer,
        "correct_answer": current_question["answer"]
    })

    # Update session with new answers list
    session["user_answers"] = user_answers

    return True, ""


def get_next_question(current_question_id):
    '''
    Fetches the next question from the PYTHON_QUESTION_LIST based on the current_question_id.
    '''
    if current_question_id is None or current_question_id == 0:
        current_question = PYTHON_QUESTION_LIST[0]
        question_text = current_question["question_text"]
        options = [f"{i+1}. {opt}" for i, opt in enumerate(current_question["options"])]
        options_text = '\n'.join(options)  
        return f"""
{question_text}

Please choose from the following options:
{options_text}
""", 1
    else:
        next_question_id = current_question_id + 1

        if next_question_id > len(PYTHON_QUESTION_LIST):
            return None, None

        next_question = PYTHON_QUESTION_LIST[next_question_id - 1]
        question_text = next_question["question_text"]
        options = [f"{i+1}. {opt}" for i, opt in enumerate(next_question["options"])]
        options_text = '\n'.join(options)  
        return f"""
{question_text}

Please choose from the following options:
{options_text}
""", next_question_id


def generate_final_response(session):
    '''
    Creates a final result message including a score based on the answers
    by the user for questions in the PYTHON_QUESTION_LIST.
    '''
    # Retrieve user answers
    user_answers = session.get("user_answers", [])

    # Calculate score
    total_questions = len(PYTHON_QUESTION_LIST)
    correct_answers = sum(
        1 for answer in user_answers if answer["user_answer"] == answer["correct_answer"])
    score_percentage = (correct_answers / total_questions) * 100

    # Generate response based on score
    if score_percentage == 100:
        performance = "Perfect! You're a Python expert!"
    elif score_percentage >= 80:
        performance = "Great job! You have a strong understanding of Python."
    elif score_percentage >= 60:
        performance = "Good effort. You have a decent understanding of Python."
    elif score_percentage >= 40:
        performance = "Not bad, but you could improve. Keep learning!"
    else:
        performance = "You might want to review Python basics."

    # Detailed breakdown
    response = f"Quiz Completed!\n\n"
    response += f"Your Score: {correct_answers}/{total_questions} ({score_percentage:.1f}%)\n\n"
    response += f"{performance}\n\n"

    # Add detailed answer breakdown
    response += "Detailed Results:\n"
    for i, answer in enumerate(user_answers, 1):
        status = "Correct ✓" if answer["user_answer"] == answer["correct_answer"] else "Incorrect ✗"
        response += f"Q{i}: {status} (Your answer: {answer['user_answer']}, Correct answer: {answer['correct_answer']})\n"

    return response
