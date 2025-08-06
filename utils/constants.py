"""Shared constants for column normalisation and other utilities."""

# Mapping of various Garmin export column names to a normalised snake_case form
# used throughout the application. This allows pages and utilities to rely on
# consistent column names regardless of the source CSV variations.
COLUMN_NORMALIZATION_MAP = {
    "Session Name": "session_name",
    "Club": "club",
    "Club Type": "club",
    "Carry Distance": "carry_distance",
    "Carry": "carry_distance",
    "Total Distance": "total_distance",
    "Ball Speed": "ball_speed",
    "Launch Angle": "launch_angle",
    "Backspin": "spin_rate",
    "Spin Rate": "spin_rate",
    "Apex Height": "apex_height",
    "Apex": "apex_height",
    "Side": "side_distance",
    "Side Distance": "side_distance",
    "Offline Distance": "offline_distance",
    "Offline": "offline_distance",
    "Session ID": "session_id",
    "Source File": "source_file",
}
