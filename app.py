import os
import re
import textwrap
import streamlit as st
from dotenv import load_dotenv
from groq import Groq, APIConnectionError, APIStatusError, RateLimitError

load_dotenv()

# --------------------------------------------------
# Section 1: Generate workout plan using Groq AI
# --------------------------------------------------

def generate_workout_plan(prompt: str) -> str:

    api_key: str | None = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError("Groq API key is missing.")

    model: str | None = os.getenv("GROQ_MODEL")

    if not model:
        raise RuntimeError("Groq Model is missing.")

    client = Groq(
        api_key=api_key,
        timeout=30.0,
        max_retries=2,
    )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a fitness workout planning assistant. "
                        "Follow the user's equipment, schedule, experience, "
                        "and limitation constraints."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.3,
            max_completion_tokens=1500,
            reasoning_effort="low",
        )

        if not response.choices:
            raise RuntimeError(
                "The AI returned an empty response. Please try again."
            )

        answer = response.choices[0].message.content
        
        if not isinstance(answer, str) or not answer.strip():
            raise RuntimeError(
                "The AI returned an empty or invalid response. "
                "Please try again."
            )
        return answer.strip()

    except RateLimitError as exc:
        raise RuntimeError("Groq rate limit reached. Please try again later.") from exc

    except APIConnectionError as exc:
        raise RuntimeError("Unable to connect to Groq. Check your internet connection.") from exc

    except APIStatusError as exc:
        raise RuntimeError(
            f"Groq API request failed (HTTP {exc.status_code}). "
            "Check your API key, model, and API access."
        ) from exc

# --------------------------------------------------

# Section 2: Build the workout prompt

# --------------------------------------------------

def build_workout_prompt(
    goal: str,
    experience: str,
    days_per_week: int,
    equipment: list[str],
    limitations: str,
    variation: int = 1,
) -> str:

    """Build a detailed prompt for a personalized workout plan."""

    prompt: str = f"""
        You are a fitness workout planning assistant.
        Create a practical weekly workout plan using these user preferences.

        USER PROFILE
        - Fitness goal: {goal}
        - Experience level: {experience}
        - Available workout days: {days_per_week}
        - Available equipment: {equipment}
        - Injuries or limitations: {limitations.strip() or "None provided"}

        PLAN VARIATION
        - Variation number: {variation}
        - If this is a new variation, make meaningful changes to exercises or the workout split where appropriate.
        - Preserve the user's goal, experience, schedule, equipment and limitations.

        REQUIREMENTS
        1. Create exactly {days_per_week} workout days per week.
        2. Match exercise difficulty to the user's experience level.
        3. Use only exercises that can be performed with the available equipment.
        4. Respect the stated injuries and limitations. Avoid exercises that directly conflict with those restrictions.
        5. Include a warm-up, exercises, sets, repetitions or duration, and rest periods.
        6. Explain which days are workout days and which are recovery days.
        7. Provide a short progression recommendation appropriate to the user's experience level and goal.
        8. Format the response with headings for each day and bullet points for exercises. Avoid one long paragraph.
        9. Do not diagnose, treat, or make medical claims about injuries.
        10. If injuries or limitations are provided, include a brief disclaimer recommending professional guidance where appropriate.
        11. Use beginner-friendly language to explain workout instructions.
        12. Write "4 sets of 8 repetitions" instead of only "4 x 8".
        13. Explain "one-rep maximum (1RM)" the first time it appears.
        14. Write "Rest for 90 seconds between sets" instead of "90 s rest".
        15. Format each exercise name in Markdown bold, for example: **Bench Press (Barbell)**.
        16. Never use the label "Exercise" before an exercise name.
        17. Do not include literal backslashes before Markdown asterisks.
        18. When weight intensity is relevant, include the percentage and explain it clearly, for example: "70% of your one-rep maximum (1RM)".
        Return only the workout plan, with clear Markdown formatting.
    """
    return textwrap.dedent(prompt).strip()

# --------------------------------------------------
# Feature 4A: Extract exercises from the workout plan
# --------------------------------------------------

def extract_exercises(plan: str) -> list[str]:
    """Return the original exercise lines so they can be matched in the plan."""

    exercises = []

    for original_line in plan.splitlines():
        line = original_line.strip()

        # Match Markdown bullet or numbered list items.
        match = re.match(r"^([-*+]|\d+[.)])\s+(.*)$", line)

        if not match:
            continue

        content = match.group(2).strip()

        # Clean a copy only for checking the line's contents.
        clean_content = content.replace(r"\*", "").replace("**", "").strip()
        clean_content = re.sub(
            r"^Exercise\s*[–—:-]\s*",
            "",
            clean_content,
            flags=re.IGNORECASE,
        )

        # Exclude warm-ups, cool-downs, and recovery instructions.
        if re.match(
            r"^(warm[- ]?up|cool[- ]?down|rest|recovery)\b",
            clean_content,
            re.IGNORECASE,
        ):
            continue

        # Keep lines that appear to describe an exercise prescription.
        details_pattern = (
            r"\b(sets?|reps?|repetitions?|seconds?|minutes?|rounds?)\b"
            r"|[×x]\s*\d"
        )

        if re.search(details_pattern, clean_content, re.IGNORECASE):
            # Skip lines that contain only sets, repetitions, or rest instructions.
            details_only = re.fullmatch(
                r"(?i)(?:(?:\d+\s+)?sets?\b.*|"
                r"\d+\s*(?:reps?|repetitions?)\b.*|"
                r"rest\b.*)",
                clean_content.strip(),
            )

            if details_only:
                continue

            # Require a plausible exercise name before the workout details.
            name_and_details = re.split(
                r"\s+[–—-]\s+",
                clean_content,
                maxsplit=1,
            )

            if len(name_and_details) == 2 and name_and_details[0].strip():
                exercises.append(line)

    return list(dict.fromkeys(exercises))

# --------------------------------------------------
# Feature 4B: Generate one replacement exercise
# --------------------------------------------------
def generate_exercise_replacement(
    selected_exercise: str,
    goal: str,
    experience: str,
    equipment: list[str],
    limitations: str,
) -> str:
    """Generate one alternative exercise using the existing Groq function."""

    prompt = f"""
    
    Suggest exactly ONE replacement for the exercise below.
    CURRENT EXERCISE:
    {selected_exercise}

    USER PROFILE:
    - Fitness goal: {goal}
    - Experience level: {experience}
    - Available equipment: {", ".join(equipment)}
    - Injuries or limitations: {limitations.strip() or "None provided"}

    REQUIREMENTS
        1. Suggest a different exercise that targets a similar muscle group or serves a similar fitness purpose.
        2. Use only the equipment available to the user.
        3. Respect the user's stated injuries and physical limitations.
        4. Keep the sets, repetitions, duration, and rest period similar to the original exercise where appropriate.
        5. Return exactly one replacement exercise, including its sets, repetitions or duration, and rest period.
        6. Do not return the original exercise.
        7. Do not return the entire workout plan.
        8. Do not include a heading, explanation, or Markdown bullet.
        9. Format only the exercise name in Markdown bold, for example: **Dumbbell Chest Press**.
        10. Explain sets, repetitions, weight intensity, and rest periods in plain English.
        11. Expand "1RM" to "one-rep maximum" the first time it appears; do not leave the abbreviation unexplained.
        12. Return the exercise name and its details on a single line.
        13. Never prefix the exercise name with the word "Exercise".
        14. Do not include literal backslashes before Markdown asterisks.
        15. Use an em dash (—) between the exercise name and its details.
        16. When weight intensity is relevant, include the percentage and explain it clearly, for example: "70% of your one-rep maximum (1RM)".
      """
    response = generate_workout_plan(prompt)
    
    # Keep only the first non-empty line
    lines = [line.strip() for line in response.splitlines() if line.strip()]

    if not lines:
        raise RuntimeError( "The AI did not return a replacement exercise.")

    replacement = lines[0]
    
    # Remove a Markdown bullet or numbered-list prefix
    replacement = re.sub(r"^(?:[-*+]|\d+[.)])\s+", "", replacement)
    
    # Remove surrounding Markdown formatting
    replacement = replacement.strip("`* ")
    
    # Remove a Markdown bullet or numbered-list prefix if returned
    replacement = re.sub(r"^(?:[-*+]|\d+[.)])\s+", "", replacement)
    
    replacement = replacement.strip("`* ")

    if not replacement:
        raise RuntimeError("The AI returned an invalid replacement exercise.")

    # Prevent replacing an exercise with the same exercise name
    original_name = re.split(r"\s[-–—:]\s|\s+\(", re.sub(r"^(?:[-*+]|\d+[.)])\s+", "", selected_exercise), maxsplit=1)[0]
    replacement_name = re.split(r"\s[-–—:]\s|\s+\(", replacement, maxsplit=1)[0]

    if replacement_name.casefold() == original_name.casefold():
        raise RuntimeError("The AI returned the same exercise. Please try again.")
    return replacement

# --------------------------------------------------
# Section 3: Configure the Streamlit page
# --------------------------------------------------

st.set_page_config(
    page_title="Workout Plan Generator",
    page_icon="🏋️",
    layout="centered",
)

def format_exercise(exercise: str) -> str:
    """Bold the exercise name and retain its workout details."""

    # Split the exercise name from its details at an em dash
    parts = re.split(r"\s+[–—]\s+", exercise, maxsplit=1)

    if len(parts) == 2:
        name, details = parts
        return f"**{name.strip()}** — {details.strip()}"

    # If no separator exists, bold the complete exercise
    return f"**{exercise.strip()}**"


def clean_workout_markdown(plan: str) -> str:
    """Fix escaped Markdown and normalize exercise-name formatting."""

    # Convert escaped Markdown asterisks into normal Markdown.
    plan = plan.replace(r"\*\*", "**")
    plan = plan.replace(r"\*", "*")

    # Fix malformed bold prefixes such as \*\***Exercise Name**.
    plan = re.sub(r"\\?\*{2,}", "**", plan)

    # Remove an unwanted 'Exercise' label before exercise names.
    plan = re.sub(
        r"(?im)^(\s*[-*+]\s+)\*{0,2}\s*Exercise\s*\*{0,2}\s*[–—:-]\s*",
        r"\1",
        plan,
    )

    return plan

# --------------------------------------------------
# Section 4: Initialize session state
# --------------------------------------------------
if "workout_plan" not in st.session_state:
    st.session_state.workout_plan = None

if "workout_inputs" not in st.session_state:
    st.session_state.workout_inputs = None

if "workout_variation" not in st.session_state:
    st.session_state.workout_variation = 0
# --------------------------------------------------
# Section 5: Application heading
# --------------------------------------------------
st.title("🏋️ Workout Plan Generator")
st.write(
    "Generate a personalized weekly workout plan based on your goals, experience, and equipment."
)
st.divider()
# --------------------------------------------------
# Section 6: User fitness profile
# --------------------------------------------------
st.header("1. Your Fitness Profile")
goal: str = st.selectbox(
    "What is your fitness goal?",
    [
        "Build muscle",
        "Lose fat",
        "General fitness",
        "Improve endurance",
    ],
    index=None,
    placeholder="Choose your fitness goal",
)

experience: str = st.selectbox(
    "What is your experience?",
    [
        "Beginner",
        "Intermediate",
        "Advanced",
    ],
    index=None,
    placeholder="Choose your experience level",
)

# --------------------------------------------------
# Section 7: Workout schedule
# --------------------------------------------------

st.header("2. Your Workout Schedule")
days_per_week: int = st.select_slider("Select the days available per week",
    options=[1, 2, 3, 4, 5, 6, 7],
)

# --------------------------------------------------
# Section 8: Available equipment
# --------------------------------------------------

st.header("3. Available Equipment")
equipment: list[str] = st.multiselect(
    "Select your equipment access preference",
    [
        "No equipment",
        "Home dumbbells",
        "Full gym",
        "Cardio + Strength",
        "Resistance Bands",
    ],
)
# --------------------------------------------------
# Section 9: Injuries or limitations
# --------------------------------------------------
st.header("4. Injuries or Limitations (Optional)")

limitations: str = st.text_area(
    "Describe any injuries or exercise limitations",
    placeholder="Example: Bad knees, avoid jumping...",
    max_chars=1000,
)
# --------------------------------------------------
# Section 10: Generate and Regenerate buttons
# --------------------------------------------------
st.divider()

col1, col2 = st.columns(2)

with col1:
    generate_clicked = st.button(
        "Generate Workout Plan",
        type="primary",
        use_container_width=True,
    )

with col2:
    regenerate_clicked = st.button(
        "Regenerate Plan",
        disabled=not bool(st.session_state.workout_plan),
        use_container_width=True,
    )
# --------------------------------------------------
# Section 11: Generate the initial workout plan
# --------------------------------------------------
if generate_clicked:
    missing_fields = []
    
    if not goal:
        missing_fields.append("a fitness goal")

    if not experience:
        missing_fields.append("an experience level")

    if not equipment:
        missing_fields.append("at least one equipment option")

    if missing_fields:
        st.error(
            f"Please select {', '.join(missing_fields)} "
            "before generating a plan."
        )
    elif "No equipment" in equipment and len(equipment) > 1:
        st.error(
            "'No equipment' cannot be combined with other options. "
            "Please select it alone or choose other equipment."
        )
    elif "Full gym" in equipment and len(equipment) > 1:
        st.error(
            "'Full gym' already includes access to gym equipment. "
            "Please select 'Full gym' alone, or select individual equipment options."
        )    
    else:
        # Save the user's inputs for future regeneration
        st.session_state.workout_inputs = {
            "goal": goal,
            "experience": experience,
            "days_per_week": days_per_week,
            "equipment": list(equipment),
            "limitations": limitations,
        }

        # The first plan is variation 1
        variation = 1
        prompt = build_workout_prompt(
            **st.session_state.workout_inputs,
            variation=variation,
        )

        try:
            with st.spinner("Generating your workout plan..."):
                plan = generate_workout_plan(prompt)

            # Save the plan after successful generation

            st.session_state.workout_plan = plan
            st.session_state.workout_variation = variation
            
            st.rerun()
            
        except RuntimeError as exc:
            st.error(str(exc))

        except Exception:
            st.error(
                "Something unexpected went wrong while generating your workout plan. Please try again."
            )

# --------------------------------------------------
# Section 12: Regenerate using saved inputs
# --------------------------------------------------
if regenerate_clicked:
    inputs = st.session_state.workout_inputs

    if inputs is None:
        st.error("Please generate a workout plan first.")
    else:
        # Increment the variation number
        variation = st.session_state.workout_variation + 1

        prompt = build_workout_prompt(
            **inputs,
            variation=variation,
        )

        try:
            with st.spinner(
                "Generating a different workout variation..."
            ):
                plan = generate_workout_plan(prompt)
                
            # Replace the saved plan only after success

            st.session_state.workout_plan = plan
            st.session_state.workout_variation = variation

        except RuntimeError as exc:
            st.error(str(exc))

        except Exception:
            st.error(
                "Something unexpected went wrong while regenerating "
                "your workout plan. Please try again."
            )

# --------------------------------------------------
# Section 13: Swap, Display, and Download the Plan
# --------------------------------------------------

if st.session_state.workout_plan:
    st.divider()

    st.subheader(
        "Your Personalized Workout Plan "
        f"(Variation {st.session_state.workout_variation})"
    )
    
    # --------------------------------------------------
    # Feature 4C: Swap One Exercise
    # --------------------------------------------------
    st.subheader("🔄 Swap an Exercise")
    exercise_options = extract_exercises(st.session_state.workout_plan)

    if exercise_options:
        selected_exercise = st.selectbox(
            "Choose one exercise to replace",
            options=exercise_options,
            format_func=lambda item: (
                re.sub(r"^[-*+]\s+", "", item.strip())
                .replace(r"\*", "")
                .replace("**", "")
                .strip()
             ),
            key="exercise_to_swap",
        )

        if st.button("Swap this exercise", use_container_width=True):
            inputs = st.session_state.workout_inputs

            if inputs is None:
                st.error(
                    "Workout preferences are unavailable. "
                    "Please generate a new plan."
                )
            else:
                try:
                    with st.spinner("Finding a suitable replacement..."):
                        replacement = generate_exercise_replacement(
                            selected_exercise=selected_exercise,
                            goal=inputs["goal"],
                            experience=inputs["experience"],
                            equipment=inputs["equipment"],
                            limitations=inputs["limitations"],
                        )

                    # Preserve the original Markdown bullet or numbering.
                    match = re.match(
                        r"^(\s*(?:[-*+] |\d+[.)]\s+))(.*)$",
                        selected_exercise,
                    )

                    # Preserve the original bullet or numbering and bold the exercise name
                    formatted_replacement = format_exercise(replacement)

                    # Remove unwanted labels and Markdown formatting from the replacement.
                    replacement = re.sub(
                        r"^\**\s*Exercise\s*\**\s*[–—:-]\s*",
                        "",
                        replacement,
                        flags=re.IGNORECASE,
                    )
                    replacement = replacement.replace(r"\*", "").replace("**", "").strip()

                    # Bold only the exercise name, not the workout instructions.
                    parts = re.split(r"\s+[–—]\s+", replacement, maxsplit=1)

                    if len(parts) == 2:
                        exercise_name, details = parts
                        formatted_replacement = f"**{exercise_name.strip()}** — {details.strip()}"
                    else:
                        formatted_replacement = f"**{replacement}**"

                    # Preserve the original bullet or numbering.
                    match = re.match(r"^([-*+]|\d+[.)])\s+", selected_exercise)

                    replacement_line = (
                        f"{match.group(1)} {formatted_replacement}"
                        if match
                        else formatted_replacement
                    )

                    updated_plan = st.session_state.workout_plan.replace(
                        selected_exercise,
                        replacement_line,
                        1,
                    )

                    if updated_plan == st.session_state.workout_plan:
                        st.error(
                            "The selected exercise could not be found "
                            "in the saved plan."
                        )
                    else:
                        st.session_state.workout_plan = updated_plan
                        st.success(
                            f"Exercise replaced successfully: {replacement}"
                        )

                except RuntimeError as exc:
                    st.error(str(exc))
                except Exception:
                    st.error(
                        "Unable to swap the exercise. Please try again."
                    )
    else:
        st.info(
            "No exercises were detected. Make sure the workout plan contains "
            "bullet-point or numbered exercise lines with sets, reps, or duration."
        )

    # --------------------------------------------------
    # Display the current plan after any replacement
    # --------------------------------------------------
    st.divider()
    cleaned_plan = clean_workout_markdown(st.session_state.workout_plan)
    st.markdown(cleaned_plan)

    # --------------------------------------------------
    # Download the latest version of the plan
    # --------------------------------------------------
    st.download_button(
        label="📥 Download Workout Plan (.md)",
        data=cleaned_plan,
        file_name="workout_plan.md",
        mime="text/markdown",
        use_container_width=True,
    )
