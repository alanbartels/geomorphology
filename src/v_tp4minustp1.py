from matplotlib import pyplot as plt

x_vals = []
y_vals = []
colors = []

row_count = 0
for row in open(r"F:\UMB\Geomorphology\output\stats_project\20.csv", 'r'):
    if row_count == 0:
        row_count += 1
        continue
    row_count += 1
    split_row = row.split(',')
    x_vals.append(float(split_row[2]) - 17)
    y_vals.append(float(split_row[0]))
    if float(split_row[0]) < 0:
        colors.append('r')
    else:
        colors.append('b')

# Make a figure
fig = plt.figure(figsize=(9, 16))
# Make some space between the subplots4.
#plt.subplots_adjust(hspace=0.3)
# Start a subplot
ax = fig.add_subplot(1, 1, 1)
# Scatter the night time lights against the "days of study"
point = ax.scatter(y_vals, x_vals, 5, colors, marker='.')

ax.plot([0, 0], [0, 15], c='k')
ax.set_ylabel('Height (Meters)')
ax.set_xlabel('Change (Meters)')

plt.show()