from matplotlib import pyplot as plt
import matplotlib as mpl


10 / 1 0.5 3 1.5


def test_func():

    return (0, 2)

(minx, maxx) = test_func()

print(minx, maxx)

print([1, 2, 3].pop())

data = [[0, 2, 4, 5, 6, 12], [0, 2, 4, 5, 6, 12]]

fig = plt.figure(figsize=(6, 12))

ax = fig.add_subplot(1, 1, 1)

box_dict = ax.boxplot(data)


skip = True
for whisker in box_dict['whiskers']:
    if skip:
        skip = False
        continue
    else:
        skip = True
    print(whisker.get_ydata())
    ax.text(whisker.get_xdata()[0],
            whisker.get_ydata()[1] + 0.1,
            'test',
            horizontalalignment='center')



plt.show()