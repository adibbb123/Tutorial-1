import csv
import random
from pathlib import Path

import pandas as pd
import streamlit as st

# Parameters from the tutorial
GEN = 100
POP = 50
CO_R = 0.8
MUT_R = 0.2
EL_S = 2

ALL_TIME_SLOTS = list(range(6, 24))
CSV_PATH = Path(__file__).resolve().parent / "program_ratings_modified.csv"


def read_csv_to_dict(file_path):
    program_ratings = {}
    with open(file_path, mode="r", newline="", encoding="utf-8-sig") as file:
        reader = csv.reader(file)
        next(reader)
        for row in reader:
            if not row:
                continue
            program = row[0]
            rating_values = []
            for value in row[1:]:
                rating_values.append(float(value))
            program_ratings[program] = rating_values
    return program_ratings


def fitness_function(schedule, ratings):
    total_rating = 0
    for index, program in enumerate(schedule):
        total_rating += ratings[program][index]
    return total_rating


def initialize_pop(programs, time_slots, population_size):
    population = []
    for i in range(population_size):
        schedule = []
        for time_slot in time_slots:
            schedule.append(random.choice(programs))
        population.append(schedule)
    return population


def crossover(schedule1, schedule2):
    crossover_point = random.randint(1, len(schedule1) - 1)
    child1 = schedule1[:crossover_point] + schedule2[crossover_point:]
    child2 = schedule2[:crossover_point] + schedule1[crossover_point:]
    return child1, child2


def mutate(schedule, programs):
    mutation_point = random.randint(0, len(schedule) - 1)
    schedule[mutation_point] = random.choice(programs)
    return schedule


def genetic_algorithm(ratings, crossover_rate, mutation_rate):
    programs = list(ratings.keys())
    population = initialize_pop(programs, ALL_TIME_SLOTS, POP)

    for generation in range(GEN):
        population.sort(
            key=lambda schedule: fitness_function(schedule, ratings),
            reverse=True
        )
        new_population = []
        for i in range(EL_S):
            new_population.append(population[i].copy())

        top_half = population[:max(2, POP // 2)]
        while len(new_population) < POP:
            parent1 = random.choice(top_half)
            parent2 = random.choice(top_half)

            if random.random() < crossover_rate:
                child1, child2 = crossover(parent1, parent2)
            else:
                child1, child2 = parent1.copy(), parent2.copy()

            if random.random() < mutation_rate:
                mutate(child1, programs)
            if random.random() < mutation_rate:
                mutate(child2, programs)

            new_population.append(child1)
            if len(new_population) < POP:
                new_population.append(child2)

        population = new_population

    population.sort(
        key=lambda schedule: fitness_function(schedule, ratings),
        reverse=True
    )
    return population[0]


st.title("TV Scheduling Using Genetic Algorithm")
st.write("Choose the Genetic Algorithm parameters and generate a TV schedule.")

try:
    ratings = read_csv_to_dict(CSV_PATH)
except FileNotFoundError:
    st.error("Cannot find program_ratings_modified.csv. Put it in the same folder as app.py.")
    st.stop()
except (ValueError, IndexError) as error:
    st.error(f"Cannot read the ratings CSV: {error}")
    st.stop()

if not ratings:
    st.error("The CSV file does not contain any programs.")
    st.stop()

for program, values in ratings.items():
    if len(values) != len(ALL_TIME_SLOTS):
        st.error(f"{program} must have 18 hourly ratings (6:00–23:00).")
        st.stop()

st.subheader("Genetic Algorithm Parameters")
crossover_rate = st.slider(
    "Crossover Rate (CO_R)",
    min_value=0.0,
    max_value=0.95,
    value=CO_R,
    step=0.01
)

mutation_option = st.radio(
    "Mutation Rate (MUT_R)",
    options=["Default (0.20)", "Change within 0.01–0.05"],
    index=0
)
if mutation_option == "Default (0.20)":
    mutation_rate = MUT_R
else:
    mutation_rate = st.slider(
        "Choose Mutation Rate",
        min_value=0.01,
        max_value=0.05,
        value=0.03,
        step=0.01
    )

if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "trial_history" not in st.session_state:
    st.session_state.trial_history = []

if st.button("Generate Schedule", type="primary"):
    final_schedule = genetic_algorithm(ratings, crossover_rate, mutation_rate)
    total_rating = fitness_function(final_schedule, ratings)

    rows = []
    for index, program in enumerate(final_schedule):
        rows.append({
            "Time Slot": f"{ALL_TIME_SLOTS[index]:02d}:00",
            "Program": program,
            "Rating": ratings[program][index]
        })

    st.session_state.last_result = {
        "rows": rows,
        "total": total_rating,
        "crossover": crossover_rate,
        "mutation": mutation_rate
    }
    st.session_state.trial_history.append({
        "Trial": len(st.session_state.trial_history) + 1,
        "Crossover Rate": crossover_rate,
        "Mutation Rate": mutation_rate,
        "Total Rating": round(total_rating, 2)
    })

if st.session_state.last_result is not None:
    result = st.session_state.last_result
    st.subheader("Generated TV Schedule")
    st.write(f"Crossover: {result['crossover']:.2f} | Mutation: {result['mutation']:.2f}")
    st.table(pd.DataFrame(result["rows"]))
    st.metric("Total Ratings", f"{result['total']:.2f}")

if st.session_state.trial_history:
    st.subheader("Trial History")
    st.table(pd.DataFrame(st.session_state.trial_history))
    st.caption("Keep screenshots of each full schedule for the report.")

    if st.button("Clear Trial History"):
        st.session_state.trial_history = []
        st.session_state.last_result = None
        st.rerun()
