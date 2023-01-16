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
        self.colors = {
            0: "darkgrey",
            1: "#FFEDA0",
            2: "#FEB24C",
            3: "#FC4E2A",
            4: "#E31A1C",
            5: "#BD0026",
            6: "#800026",
        }
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
        weights = {"students": (1, 5), "balanced": (3, 3), "instrumentation": (5, 1)}
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
                count
                - pulp.lpSum([assignment[s][i] for s in self.students])
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
        self.preference = preference
        self.band = pd.DataFrame(assignment).applymap(pulp.value).transpose()
        return self.band

    def wrangle_band_assignments_long(
        self,
        band_assignments: pd.DataFrame,
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
        # Get Assignment Data
        df = self.wrangle_band_assignments_long(band_assignments)

        # Matrix Assignment chart.
        assignment_base = (
            alt.Chart(df)
            .encode(
                x=alt.X("instrument", sort=self.instruments, title=None),
                y=alt.Y("student", sort=self.students, title=None),
            )
            .properties(
                title={
                    "text": f"Optimal Band ({self.preference.title()})",
                    "subtitle": "Band Instrument Assignments and Preferences.",
                    "fontSize": 20,
                    "anchor": "start",
                }
            )
        )
        assignment_rectangles = assignment_base.mark_rect(
            stroke="black", strokeWidth=0.1
        ).encode(
            color=alt.Color(
                "preference:O",
                scale=alt.Scale(
                    domain=list(self.colors.keys()), range=list(self.colors.values())
                ),
                title="Student Preference",
                legend=None
            )
        )
        assignment_text = (
            assignment_base.mark_text(color="grey")
            .encode(text="preference:O")
            .transform_filter(alt.datum.preference > 0)
        )
        assignment_chart = assignment_rectangles + assignment_text

        # Instrumentation Data
        actual_counts = (
            df.query("assignment == 1.0")[["instrument"]]
            .value_counts()
            .rename("actual_count")
        )
        ideal_counts = pd.Series(self.instrument_idealcount, name="ideal_count")
        ideal_counts.index.name = "instrument"
        instrumentation = pd.merge(
            actual_counts, ideal_counts, on="instrument"
        ).reset_index()
        instrumentation["difference"] = abs(
            instrumentation["ideal_count"] - instrumentation["actual_count"]
        )
        instrumentation["fill"] = instrumentation.apply(
            lambda row: f"{row['actual_count']}/{row['ideal_count']}", axis="columns"
        )

        # Instrumentation Chart
        instrumentation_colors = {
            index - 1: color for index, color in self.colors.items()
        }
        instrumentation_base = (
            alt.Chart(instrumentation, title="instrumentation")
            .encode(
                x=alt.X(
                    "instrument",
                    sort=self.instruments,
                    title=None,
                    axis=alt.Axis(ticks=False),
                ),
                y=alt.Y("actual_count", title=None, axis=None),
            )
            .properties(height=150)
        )
        instrumentation_bars = instrumentation_base.mark_bar().encode(            
                color=alt.Color(
                    "difference",
                    scale=alt.Scale(
                        domain=list(instrumentation_colors.keys()),
                        range=list(instrumentation_colors.values()),
                    ),
                    legend=None,
                ),
        )
        instrumentation_text = instrumentation_base.mark_text(
            align="center", baseline="middle", dy=-8, color="grey"
        ).encode(
            text="fill",
        )
        instrumentation_marks = (
            instrumentation_base
            .mark_tick()
            .encode(y="ideal_count")
        )
        instrumentation_chart = instrumentation_bars + instrumentation_text + instrumentation_marks

        band_chart = assignment_chart & instrumentation_chart
        return band_chart
