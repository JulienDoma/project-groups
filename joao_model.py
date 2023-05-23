"""Model Joao made for making groups based on preferences"""
from math import ceil
import numpy as np
from scipy.optimize import linprog
import pandas as pd

def make_groups(data_df, x_c):
    # x_c is the number of extra columns for any necessary processing
    x_c = 1

    data_array = data_df.to_numpy()[:, 1:-1]
    n_projects = data_array.shape[1]
    n_students = data_array.shape[0]
    data = data_array.reshape([n_students * n_projects])

    min_projects = ceil(n_students / 4)

    col = (n_students + 1) * n_projects + x_c

    A = np.zeros([n_students, col])
    b = np.zeros(n_students)

    # 1 project per person
    for i in range(n_students):
        A[i, i * n_projects : (i + 1) * n_projects] = 1
        b[i] = 1

    # max 4 people per project
    A_ub = np.zeros([n_projects, col])
    b_ub = np.array([4] * n_projects)
    for i in range(n_projects):
        for j in range(n_students):
            A_ub[i, j * n_projects + i] = 1

    # selected project total
    temp = np.zeros([1, col])
    temp[0, -n_projects - x_c : -x_c] = -1
    A_ub = np.concatenate([A_ub, temp])
    b_ub = np.concatenate([b_ub, [-min_projects]])

    # project can only be selected once
    temp = np.zeros([n_projects, col])
    for i in range(n_projects):
        temp[i, col - x_c - n_projects + i] = 1
    A_ub = np.concatenate([A_ub, temp])
    b_ub = np.concatenate([b_ub, [1] * n_projects])

    # selected project totals match selections
    temp = np.zeros([n_projects, col])
    for i in range(n_projects):
        for j in range(n_students):
            temp[i, j * n_projects + i] = -1
        temp[i, col - x_c - n_projects + i] = 4
    A_ub = np.concatenate([A_ub, temp])
    b_ub = np.concatenate([b_ub, [1] * n_projects])
    temp = np.zeros([n_projects, col])
    for i in range(n_projects):
        for j in range(n_students):
            temp[i, j * n_projects + i] = 1
        temp[i, col - x_c - n_projects + i] = -4
    A_ub = np.concatenate([A_ub, temp])
    b_ub = np.concatenate([b_ub, [0] * n_projects])

    # minimax pref
    temp = np.zeros([n_students * n_projects, col])
    for i in range(n_students):
        for j in range(n_projects):
            temp[i * n_projects + j, i * n_projects + j] = data[i * n_projects + j]
            temp[i * n_projects + j, col - x_c] = -1

    A_ub = np.concatenate([A_ub, temp])
    b_ub = np.concatenate([b_ub, [0] * n_students * n_projects])

    c = np.zeros(col)
    c[col - x_c] = 1

    res = linprog(c, A_eq=A, b_eq=b, A_ub=A_ub, b_ub=b_ub, integrality=1)

    print(
        "Optimal Value: ",
        round(res.fun, ndigits=2),
        "\nx Values: ",
        res.x,
        "\nNumber of iterations performed: ",
        res.nit,
        "\nStatus: ",
        res.message,
    )

    # setting best result as constraint
    temp = np.zeros([1, col])
    temp[0, col - x_c] = 1
    A_ub = np.concatenate([A_ub, temp])
    b_ub = np.concatenate([b_ub, [res.x[-1]]])

    # minimizing total pref
    c = np.concatenate([data, [0] * (n_projects + 1)])
    res = linprog(c, A_eq=A, b_eq=b, A_ub=A_ub, b_ub=b_ub, integrality=1)

    print(
        "Optimal value:",
        round(res.fun, ndigits=2),
        "\nx values:",
        res.x,
        "\nNumber of iterations performed:",
        res.nit,
        "\nStatus:",
        res.message,
    )

    print("Results: ")
    print(
        (res.x[: -n_projects - x_c] * data)
        .reshape([n_students, n_projects])
        .astype(int)
    )

    print("\nChosen Projects: ")
    print(res.x[-n_projects - x_c : -x_c])

    res_df = pd.DataFrame(
        (res.x[: -n_projects - x_c] * data).reshape([n_students, n_projects]).astype(int)
    )

    return res_df