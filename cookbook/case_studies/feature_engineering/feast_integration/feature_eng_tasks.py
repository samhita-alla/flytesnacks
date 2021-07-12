"""
Feature Engineering Tasks
-------------------------

We'll define the relevant feature engineering tasks to clean up the SQLite3 data.
"""

# %%
# First, let's import the required libraries.
import numpy as np
import pandas as pd
from flytekit import task
from flytekit.types.schema import FlyteSchema
from numpy.core.fromnumeric import sort
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.impute import SimpleImputer

# %%
# There are a specific set of columns for which imputation isn't required. We ignore them.
NO_IMPUTATION_COLS = [
    "Hospital Number",
    "surgery",
    "Age",
    "outcome",
    "surgical lesion",
    "timestamp",
]

# %%
# Next, we define a ``mean_median_imputer`` task to fill in the missing values of the dataset, for which we use `SimpleImputer <https://scikit-learn.org/stable/modules/generated/sklearn.impute.SimpleImputer.html>`__ class from the ``scikit-learn`` library.
@task
def mean_median_imputer(
    dataframe: pd.DataFrame,
    imputation_method: str,
) -> FlyteSchema:

    dataframe = dataframe.replace("?", np.nan)
    if imputation_method not in ["median", "mean"]:
        raise ValueError("imputation_method takes only values 'median' or 'mean'")

    imputer = SimpleImputer(missing_values=np.nan, strategy=imputation_method)

    imputer = imputer.fit(
        dataframe[dataframe.columns[~dataframe.columns.isin(NO_IMPUTATION_COLS)]]
    )
    dataframe[
        dataframe.columns[~dataframe.columns.isin(NO_IMPUTATION_COLS)]
    ] = imputer.transform(
        dataframe[dataframe.columns[~dataframe.columns.isin(NO_IMPUTATION_COLS)]]
    )
    return dataframe


# %%
# Let's define the other task called ``univariate_selection`` that does feature selection.
# The `SelectKBest <https://scikit-learn.org/stable/modules/generated/sklearn.feature_selection.SelectKBest.html#sklearn.feature_selection.SelectKBest>`__ method removes all but the highest scoring features (data frame columns).
@task
def univariate_selection(
    dataframe: pd.DataFrame, num_features: int, data_class: str, feature_view_name: str
) -> pd.DataFrame:

    # Remove ``timestamp`` and ``Hospital Number`` columns as they ought to be present in the dataset
    dataframe = dataframe.drop(["event_timestamp", "Hospital Number"], axis=1)

    if num_features > 9:
        raise ValueError(
            f"Number of features must be <= 9; you've given {num_features}"
        )

    X = dataframe.iloc[:, dataframe.columns != data_class]
    y = dataframe.loc[:, feature_view_name + "__" + data_class]
    test = SelectKBest(score_func=f_classif, k=num_features)
    fit = test.fit(X, y)
    indices = sort((-fit.scores_).argsort()[:num_features])
    column_names = map(dataframe.columns.__getitem__, indices)
    features = fit.transform(X)
    final_df = pd.DataFrame(features, columns=column_names)
    return final_df


# %%
# The aforementioned feature engineering tasks are used as ``reference tasks`` while building the Flyte pipeline with Feast.