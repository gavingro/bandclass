from typing import Dict, Literal, List, Optional
from time import time
import logging

import pulp
import pandas as pd
import altair as alt
from numpy import floor, ceil


class BandClassLP:
    """
    A helper class to create an ideal band class instrument assignment.
    """

    def __init__(
        self,
        instrument_idealcount: Dict[str, int],
        student_preferences: Dict[str, List[str]],
    ):
        self.instrument_idealcount = instrument_idealcount
        self.student_preferences = student_preferences
        self.instruments = list(instrument_idealcount.keys())
        self.idealcounts = list(instrument_idealcount.values())
        self.students = list(student_preferences.keys())
        self.preferences = list(student_preferences.values())
        self.num_instruments = len(self.instruments)
        self.num_students = len(self.students)
        """
        A helper class to create an ideal band class instrument assignment.
        
        Parameters
        ----------
        instrument_idealcount : Dict[str, int]
            A dictionary containing all of the instruments the students may 
            select from, and their ideal count in the final band.

        student_preferences : Dict[str, List[str]]
            A dictionary containing all of the student names in the final band,
            and a list of each of the instruments they are willing to play 
            in order of preference.
        """

    def get_optimal_band(
        self,
        preference: Literal["students", "balanced", "instrumentation"] = "balanced",
    ) -> pd.DataFrame:
        """
        Creates an optimal band through solving a linear programming problem
        setup with Pulp.

        Parameters
        ----------
        preference : str, optional
            Controls weather to give preference to the students choices,
            the instrumentation needs, or a balance of both,
            by default "balanced".

        Returns
        -------
        pd.DataFrame
            The band assignment solutions to the linear programming problem.
        """
        weights = {"students": (1, 5), "balanced": (3, 3), "instrumentation": (3, 1)}
        composition_weight, preference_weight = weights[preference]

        problem = pulp.LpProblem(name=f"BandClassLp-{preference}")
        # Setup Matrix of Parameters.
        assignment = pulp.LpVariable.dicts(
            "Assignment",
            (self.students, self.instruments),
            lowBound=0,
            upBound=1,
            cat=pulp.LpInteger,
        )

        # CONSTRAINTS:
        # Constraint 1: 1 instrument per person.
        for s in self.students:
            problem += (
                pulp.lpSum([assignment[s][i] for i in self.instruments]) == 1,
                f"{s}_will_play_1_instrument.",
            )

        # Constraint 2: Lower limit on instrumentation.
        if preference != "students":
            for i in self.instruments:
                problem += (
                    pulp.lpSum([assignment[s][i] for s in self.students])
                    >= floor(0.75 * self.instrument_idealcount[i]),
                    f"More_than_{1.5 * self.instrument_idealcount[i]}_{i}.",
                )

        # Constraint 3: No non-selected instruments for each person.
        for s in self.students:
            selected_instrument = self.student_preferences[s]
            non_selected_instruments = [
                instrument
                for instrument in self.instruments
                if instrument not in selected_instrument
            ]
            problem += (
                pulp.lpSum([assignment[s][i] for i in non_selected_instruments]) == 0,
                f"{s}_instrument_selection",
            )

        # Constraint 4: Upper limit on instrumentation.
        if preference != "students":
            for i in self.instruments:
                problem += (
                    pulp.lpSum([assignment[s][i] for s in self.students])
                    <= ceil(1.5 * self.instrument_idealcount[i]),
                    f"Less_than_{1.5 * self.instrument_idealcount[i]}_{i}.",
                )

        # OBJECTIVE:
        obj = 0

        # Ideal Band Composition:
        # TODO: THIS HACK DOESN'T WORK AND GIVES BONUS FOR EXTRAS?.
        # (count - assigned_count) is not always positive.
        # Temporary patchwork with lower and upper constraints.
        for i, count in self.instrument_idealcount.items():
            obj += (
                count - pulp.lpSum([assignment[s][i] for s in self.students])
                * composition_weight
            )

        # Student Preferred Instruments:
        for s, preferences in self.student_preferences.items():
            obj += (
                pulp.lpSum(
                    [assignment[s][i] * (preferences.index(i)) for i in preferences]
                )
                * preference_weight
            )

        problem += obj

        # Solve and get results.
        start = time()
        status = problem.solve()
        end = time()
        seconds = end - start
        logging.info(
            "Status:",
            "Success"
            if status == 1
            else "failure: proximity to ideal instrument counts impossible with current student preferences.",
        )
        logging.info(
            "Seconds:" if seconds > 1 else "Milliseconds:",
            round(seconds, 2) if seconds > 1 else int(seconds * 1000),
        )
        self.band = pd.DataFrame(assignment).applymap(pulp.value).transpose()
        return self.band

    def wrangle_band_assignments_long(
        self, band_assignments: pd.DataFrame
    ) -> pd.DataFrame:
        """Melts wide df into long-form and adds preference column."""
        df = (
            band_assignments.melt(
                var_name="instrument", ignore_index=False, value_name="assignment"
            )
            .reset_index()
            .rename(columns={"index": "student"})
        )
        df["preference"] = df.apply(
            lambda row: self.student_preferences[row.student].index(row.instrument)
            + 1  # +1 to offset indexing
            if row.assignment
            else 0,
            axis=1,
        )
        return df

    def display_band(
        self, band_assignments: Optional[pd.DataFrame] = None
    ) -> alt.Chart:
        """A helper function to display the assignment results of optimal band
        created get_optimal_band"""
        if band_assignments is not None and not self.band:
            raise ValueError(
                "Either band_assignments or self.band is required to display results."
            )
        elif not band_assignments:
            band_assignments = self.band

        df = self.wrangle_band_assignments_long(band_assignments)

        basechart = (
            alt.Chart(df)
            .encode(
                x=alt.X("instrument", sort=self.instruments, title=None),
                y=alt.Y("student", sort=self.students, title=None),
            )
            .properties(
                title={
                    "text": "Optimal Band Assignment.",
                    "subtitle": "Student Instrument Assignments and Preferences.",
                    "fontSize": 20,
                    "anchor": "start",
                }
            )
        )
        chart_rectangles = basechart.mark_rect(stroke="black", strokeWidth=0.1).encode(
            color=alt.Color(
                "preference:O",
                scale=alt.Scale(scheme="redgrey", reverse=True),
                title="Instrument Preference",
            )
        )

        chart_text = (
            basechart.mark_text(color="grey")
            .encode(text="preference:O")
            .transform_filter(alt.datum.preference > 0)
        )
        return chart_rectangles + chart_text
