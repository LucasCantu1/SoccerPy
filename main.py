import numpy as np
from mplsoccer import Pitch, Sbopen
from statsbombpy import sb
import pandas as pd
import matplotlib.pyplot as plt


def get_team_match_ids(name_team):
    # This function return the match id list of some team
    # The matches are from  FIFA world cup 2022
    matches = sb.matches(competition_id=43, season_id=106)
    matches = matches[(matches["home_team"] == name_team) | (matches["away_team"] == name_team)]
    # List of the ids
    matches_list = matches["match_id"].to_list()
    return matches_list


def get_shots_df(match_id):
    # This function uses the parser from mplsoccer to get a dataframe of all shots of a match
    parser = Sbopen()
    df, related, freeze, tactics = parser.event(match_id)
    # A dataframe of shots
    shots = df.loc[df['type_name'] == 'Shot'].set_index('id')
    return shots


def get_pass_df(match_id):
    # This function uses the parser from mplsoccer to get a dataframe of all passes of a match
    parser = Sbopen()
    df, related, freeze, tactics = parser.event(match_id)
    # A dataframe of passes
    passes = df.loc[df['type_name'] == 'Pass'].loc[df['sub_type_name'] != 'Throw-in'].set_index('id')
    return passes


def pitch_map(home_team_name):
    # This function plots a figure with all shots of certain team in the competition
    pitch = Pitch(line_color="black", pitch_color="grass", stripe=True)
    fig, ax = pitch.draw(figsize=(10, 7))
    # Size of the pitch in yards (FIFA standard)
    pitchlenghtx = 120
    pitchwidhty = 80
    # Plot the shots by looping through them and the matches.
    for match_id in get_team_match_ids(home_team_name):
        shots = get_shots_df(match_id)
        for row, shot in shots.iterrows():
            # get the information (Coordinates of the shot)
            x = shot['x']
            y = shot['y']
            # Variable to determine if the goal happened
            goal = shot['outcome_name'] == 'Goal'
            team_name = shot['team_name']
            # set circle size
            circle_size = 1.5
            # plot home_team
            if team_name == home_team_name:
                if goal:
                    shot_circle = plt.Circle((x, y), circle_size, color="red")
                else:
                    shot_circle = plt.Circle((x, y), circle_size, color="red")
                    shot_circle.set_alpha(.2)
            # plot the other team
            else:
                if goal:
                    shot_circle = plt.Circle((pitchlenghtx - x, pitchwidhty - y), circle_size, color="blue")
                else:
                    shot_circle = plt.Circle((pitchlenghtx - x, pitchwidhty - y), circle_size, color="blue")
                    shot_circle.set_alpha(.2)
            ax.add_patch(shot_circle)
    # set title
    fig.suptitle(f"{home_team_name} (red) and others (blue) shots", fontsize=12)
    fig.set_size_inches(10, 7)
    return ax


def passes_player(player, match_id):
    # This function shows the passes of a player during a match
    passes = get_pass_df(match_id)
    # Get the unique names of the teams
    team1, team2 = passes.team_name.unique()
    # drawing pitch
    pitch = Pitch(line_color="black")
    fig, ax = pitch.draw(figsize=(10, 7))

    for row, THEPASS in passes.iterrows():
        # if pass made by the selected player
        if THEPASS['player_name'] == player:
            # Coordinates of the pass
            x = THEPASS['x']
            y = THEPASS['y']
            # plot circle
            pass_circle = plt.Circle((x, y), 2, color="blue")
            pass_circle.set_alpha(.2)
            ax.add_patch(pass_circle)
            dx = THEPASS['end_x'] - x
            dy = THEPASS['end_y'] - y
            # plot arrow
            pass_arrow = plt.Arrow(x, y, dx, dy, width=3, color="blue")
            ax.add_patch(pass_arrow)

    ax.set_title(f"{player} passes against {team1}", fontsize=24)
    fig.set_size_inches(10, 7)
    return ax


def grid_passes(match_id, team_name):
    parser = Sbopen()
    df, related, freeze, tactics = parser.event(match_id)
    grid_data = (df.type_name == 'Pass') & (df.team_name == team_name) & (df.sub_type_name != "Throw-in")
    df_passes = df.loc[grid_data, ['x', 'y', 'end_x', 'end_y', 'player_name']]
    # get the list of all players who made a pass
    names = df_passes['player_name'].unique()

    # Getting the team names
    team = df.team_name.unique()
    team2 = np.setdiff1d(team, team_name)[0]

    # draw 4x4 pitches
    pitch = Pitch(line_color='black', pad_top=20)
    fig, axs = pitch.grid(ncols=4, nrows=4, grid_height=0.85, title_height=0.06, axis=False,
                          endnote_height=0.04, title_space=0.04, endnote_space=0.01)

    # for each player
    for name, ax in zip(names, axs['pitch'].flat[:len(names)]):
        # put player name over the plot
        ax.text(60, -10, name,
                ha='center', va='center', fontsize=14)
        # take only passes by this player
        player_df = df_passes.loc[df_passes["player_name"] == name]
        # scatter
        pitch.scatter(player_df.x, player_df.y, alpha=0.2, s=50, color="blue", ax=ax)
        # plot arrow
        pitch.arrows(player_df.x, player_df.y,
                     player_df.end_x, player_df.end_y, color="blue", ax=ax, width=1)

    # We have more than enough pitches - remove them
    for ax in axs['pitch'][-1, 16 - len(names):]:
        ax.remove()

    # Another way to set title using mplsoccer
    axs['title'].text(0.5, 0.5, f'{team_name} passes against {team2}', ha='center', va='center', fontsize=30)
    return axs


def pass_network(match_id, team_name):
    parser = Sbopen()
    df, related, freeze, tactics = parser.event(match_id)
    # Getting the team names
    team = df.team_name.unique()
    team2 = np.setdiff1d(team, team_name)[0]
    # check for index of first sub
    sub = df.loc[df["type_name"] == "Substitution"].loc[df["team_name"] == team_name].iloc[0]["index"]
    # make df with successfully passes by England until the first substitution
    mask_team = (df.type_name == 'Pass') & (df.team_name == team_name) & (df.index < sub) & (
        df.outcome_name.isnull()) & (df.sub_type_name != "Throw-in")
    # taking necessary columns
    df_pass = df.loc[mask_team, ['x', 'y', 'end_x', 'end_y', "player_name", "pass_recipient_name"]]
    # adjusting that only the surname of a player is presented.
    df_pass["player_name"] = df_pass["player_name"].apply(lambda x: str(x).split()[-1])
    df_pass["pass_recipient_name"] = df_pass["pass_recipient_name"].apply(lambda x: str(x).split()[-1])

    scatter_df = pd.DataFrame()
    for row, name in enumerate(df_pass["player_name"].unique()):
        passx = df_pass.loc[df_pass["player_name"] == name]["x"].to_numpy()
        recx = df_pass.loc[df_pass["pass_recipient_name"] == name]["end_x"].to_numpy()
        passy = df_pass.loc[df_pass["player_name"] == name]["y"].to_numpy()
        recy = df_pass.loc[df_pass["pass_recipient_name"] == name]["end_y"].to_numpy()
        scatter_df.at[row, "player_name"] = name
        # make sure that x and y location for each circle representing the player is the average of passes and
        # receptions
        scatter_df.at[row, "x"] = np.mean(np.concatenate([passx, recx]))
        scatter_df.at[row, "y"] = np.mean(np.concatenate([passy, recy]))
        # calculate number of passes
        scatter_df.at[row, "no"] = df_pass.loc[df_pass["player_name"] == name].count().iloc[0]

    # adjust the size of a circle
    scatter_df['marker_size'] = (scatter_df['no'] / scatter_df['no'].max() * 1500)
    # counting passes between players
    df_pass["pair_key"] = df_pass.apply(lambda x: "_".join(sorted([x["player_name"], x["pass_recipient_name"]])),
                                        axis=1)
    lines_df = df_pass.groupby(["pair_key"]).x.count().reset_index()
    lines_df.rename({'x': 'pass_count'}, axis='columns', inplace=True)

    # plot once again pitch and vertices
    pitch = Pitch(line_color='grey')
    fig, ax = pitch.grid(grid_height=0.9, title_height=0.06, axis=False,
                         endnote_height=0.04, title_space=0, endnote_space=0)
    pitch.scatter(scatter_df.x, scatter_df.y, s=scatter_df.marker_size, color='red', edgecolors='grey', linewidth=1,
                  alpha=1, ax=ax["pitch"], zorder=3)
    for row, row in scatter_df.iterrows():
        pitch.annotate(row.player_name, xy=(row.x, row.y), c='black', va='center', ha='center', weight="bold", size=16,
                       ax=ax["pitch"], zorder=4)

    for row, row in lines_df.iterrows():
        player1 = row["pair_key"].split("_")[0]
        player2 = row['pair_key'].split("_")[1]
        # take the average location of players to plot a line between them
        player1_x = scatter_df.loc[scatter_df["player_name"] == player1]['x'].iloc[0]
        player1_y = scatter_df.loc[scatter_df["player_name"] == player1]['y'].iloc[0]
        player2_x = scatter_df.loc[scatter_df["player_name"] == player2]['x'].iloc[0]
        player2_y = scatter_df.loc[scatter_df["player_name"] == player2]['y'].iloc[0]
        num_passes = row["pass_count"]
        # adjust the line width so that the more passes, the wider the line
        line_width = (num_passes / lines_df['pass_count'].max() * 10)
        # plot lines on the pitch
        pitch.lines(player1_x, player1_y, player2_x, player2_y,
                    alpha=1, lw=line_width, zorder=2, color="red", ax=ax["pitch"])

    fig.suptitle(f"{team_name} Passing Network against {team2}", fontsize=30)
    return ax
