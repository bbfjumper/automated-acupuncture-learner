import pickle
import random
import re
from datetime import datetime
from pathlib import Path
from tkinter import *
from tkinter import messagebox
from typing import Final

DATA_LOCATION: Final[Path] = Path(__file__).resolve().parent / "data"


class Progress:
    """
    Represents the progress of a user in answering questions.

    Attributes:
        progress (dict): A dictionary containing the progress information.
            It has the following keys:
            - "time": A list of timestamps indicating when the progress was recorded.
            - "known": A list of lists, where each inner list contains the question IDs
                that the user has answered correctly.
            - "unknown": A list of lists, where each inner list contains the question IDs
                that the user has answered incorrectly.
    """

    def __init__(self):
        self.progress = {"time": [], "known": [], "unknown": []}

    def reset_unknown(self):
        self.progress["unknown"].append([])

    def add_known(self, question_id):
        self.progress["known"][-1].append(question_id)

    def add_unknown(self, question_id):
        self.progress["unknown"][-1].append(question_id)

    def save(self):
        with open(DATA_LOCATION / "progress.pkl", "wb") as file:
            pickle.dump(self.progress, file)

    def show(self, i_questions: int):
        percentage = (len(self.progress["known"][-1]) / i_questions) * 100
        if percentage > 50:
            messagebox.showinfo(
                "Result",
                f"Congratulations! You answered {percentage:.2f}% of the questions right.",
            )
        else:
            messagebox.showinfo(
                "Result",
                f"You answered {percentage:.2f}% of the questions right.",
            )

    @classmethod
    def load(cls):
        progress_file = DATA_LOCATION / "progress.pkl"
        instance = cls()
        if progress_file.exists():
            with progress_file.open("rb") as file:
                progress = pickle.load(file)
            instance.progress = progress
        instance.progress["time"].append(datetime.now().isoformat())
        instance.progress["known"].append([])
        instance.progress["unknown"].append([])
        return instance


def _define_categories_gui(data: dict[str, list[str]]) -> list[str]:
    """
    Creates a GUI window for selecting categories from a given data dictionary.

    Args:
        data (dict[str, list[str]]): A dictionary containing category data.

    Returns:
        list[str]: A list of selected categories.

    """

    class CategorySelector(Tk):
        def __init__(self, categories):
            super().__init__()
            self.title("Select Categories")
            self.geometry("300x400")
            self.selected_categories = []
            self.check_vars = []
            Label(self, text="Select Categories:", font=("Helvetica", 16)).pack(pady=10)
            for category in categories:
                var = BooleanVar()
                chk = Checkbutton(self, text=category, variable=var)
                chk.pack(anchor="w")
                self.check_vars.append((category, var))
            Button(self, text="Submit", command=self.submit).pack(pady=20)

        def submit(self):
            self.selected_categories = [category for category, var in self.check_vars if var.get()]
            self.destroy()

    categories = list(set(data["category"]))
    selector = CategorySelector(categories)
    selector.mainloop()
    return selector.selected_categories


def _remove_non_printable_chars(s):
    """
    Removes non-printable characters from a string.

    Args:
        s (str): The input string.

    Returns:
        str: The input string with non-printable characters removed.
    """
    non_printable_pattern = re.compile(r"[^\x20-\x7E\xA0-\xFF]")
    return non_printable_pattern.sub("", s)


def _load_voc_data() -> dict[str, list[str]]:
    """
    Load vocabulary data from a CSV file and return it as a dictionary.

    Returns:
        A dictionary containing the loaded vocabulary data with the following keys:
        - 'category': A list of category names.
        - 'question': A list of question strings.
        - 'answer': A list of answer strings.
        - 'id': A list of IDs corresponding to each question-answer pair.
    """
    fname = DATA_LOCATION / "real_data.csv"
    voc_data = {"category": [], "question": [], "answer": []}

    with open(fname, "r", encoding="utf-8") as f:
        for line in f:
            stripped_line = line.strip()
            if not stripped_line:
                continue
            cleaned_line = _remove_non_printable_chars(stripped_line)
            parts = cleaned_line.split(";", 2)
            if len(parts) != 3:
                continue
            category, question, answer = parts
            voc_data["category"].append(category)
            voc_data["question"].append(question)
            voc_data["answer"].append(answer)

    voc_data["id"] = list(range(len(voc_data["question"])))
    return voc_data


class VocabularyTrainer(Tk):
    def __init__(self, data, categories):
        super().__init__()
        self.data = data
        self.categories = categories
        self.progress = Progress.load()
        self.indices = [i for i in range(len(data["question"])) if data["category"][i] in categories]
        random.shuffle(self.indices)
        self.current_index = 0
        self.sum_of_questions = len(self.indices)
        self.title("Akupunktur Trainer")
        self.geometry("600x400")
        self.show_result = True
        self.create_widgets()
        self.show_question()

    def create_widgets(self):
        self.frame_question = Frame(self)
        self.frame_question.pack(pady=10)

        self.label_question = Label(self.frame_question, text="", wraplength=500, font=("Helvetica", 14))
        self.label_question.pack()

        self.frame_answer = Frame(self)
        self.frame_answer.pack(pady=10)

        self.entry_answer = Entry(self.frame_answer, font=("Helvetica", 14), width=50)
        self.entry_answer.pack(padx=10, pady=10)

        self.button_submit = Button(
            self.frame_answer, text="Submit", command=self.submit_answer, font=("Helvetica", 12)
        )
        self.button_submit.pack(pady=10)

        self.frame_result = Frame(self)
        self.frame_result.pack(pady=10)

        self.label_correct_answer = Label(self.frame_result, text="", font=("Helvetica", 12), wraplength=500)
        self.label_correct_answer.pack()

        self.frame_decision = Frame(self)
        self.frame_decision.pack(pady=10)

        self.button_right = Button(
            self.frame_decision,
            text="Right",
            command=lambda: self.record_answer(True),
            font=("Helvetica", 12),
            width=10,
            state=DISABLED,
        )
        self.button_right.pack(side=LEFT, padx=20, pady=20)

        self.button_wrong = Button(
            self.frame_decision,
            text="Wrong",
            command=lambda: self.record_answer(False),
            font=("Helvetica", 12),
            width=10,
            state=DISABLED,
        )
        self.button_wrong.pack(side=RIGHT, padx=20, pady=20)

    def show_question(self):
        if self.current_index < self.sum_of_questions:
            question_id = self.indices[self.current_index]
            question = self.data["question"][question_id]
            self.label_question.config(text=f"Question {self.current_index + 1}/{self.sum_of_questions}: {question}")
            self.entry_answer.delete(0, END)
            self.label_correct_answer.config(text="")
            self.button_right.config(state=DISABLED)
            self.button_wrong.config(state=DISABLED)
        else:
            if self.show_result:
                self.progress.show(self.sum_of_questions)
                self.show_result = False
            if self.progress.progress["unknown"][-1] and messagebox.askyesno(
                "Retry?", "Do you want to retry the incorrectly answered questions?"
            ):
                self.indices = self.progress.progress["unknown"][-1]
                self.progress.reset_unknown()
                self.sum_of_questions = len(self.indices)
                self.current_index = 0
                self.show_question()
            else:
                self.destroy()

    def submit_answer(self):
        question_id = self.indices[self.current_index]
        correct_answer = self.data["answer"][question_id]
        self.label_correct_answer.config(text=f"Correct answer: {correct_answer}")
        self.button_right.config(state=NORMAL)
        self.button_wrong.config(state=NORMAL)

    def record_answer(self, is_known):
        question_id = self.indices[self.current_index]
        if is_known:
            self.progress.add_known(question_id)
        else:
            self.progress.add_unknown(question_id)
        self.progress.save()
        self.current_index += 1
        self.show_question()


if __name__ == "__main__":
    try:
        data = _load_voc_data()
        categories = _define_categories_gui(data)
        if categories:
            app = VocabularyTrainer(data, categories)
            app.mainloop()
        else:
            messagebox.showinfo("No Categories Selected", "No categories were selected. Exiting...")
    except Exception as e:
        messagebox.showerror("Error", str(e))
