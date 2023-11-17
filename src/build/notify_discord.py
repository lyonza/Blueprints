"""
Python script to be called by a GitHub action.

This script parses the Github Issue JSON contained in the GITHUB_CONTEXT
environment variable. It parses this content and then posts a message
on the Discord Webhook describing the created Blueprint.
"""


from datetime import datetime, timedelta
from os import environ
from sys import exit as sys_exit

from discord_webhook import DiscordWebhook, DiscordEmbed

from src.build.parse_submission import parse_submission


DEFAULT_AVATAR_URL = (
    'https://raw.githubusercontent.com/CollinHeist/static/main/logo.png'
)


def get_next_merge_time() -> datetime:
    """
    Get the next time in which the the automated Blueprint merging
    workflow will run.

    Returns:
        The next time in which merging will occur.
    """

    now = datetime.now()
    nearest_4hr = now.replace(
        hour=now.hour // 4 * 4,
        minute=0, second=0, microsecond=0,
    )

    return nearest_4hr + timedelta(hours=4)


def format_timedelta(delta: timedelta) -> str:
    """
    Format the given timedelta into human readable text.

    >>> format_timedelta(timedelta(hours=4, minutes=12))
    '4 hours, and 12 minutes'
    >>> format_timedelta(timedelta(hours=1, minutes=1))
    '1 minute'

    Args:
        delta: The timedelta to format.

    Returns:
        The formatted time string of the given delta.
    """

    hours, seconds = divmod(delta.total_seconds(), 3600)
    minutes = int(seconds // 60)

    output = ''
    if (hours := int(hours)) > 0:
        output += f'{hours} hour{"s" if hours > 1 else ""}'

    if minutes > 0:
        if output:
            output += ', and '
        output += f'{minutes} minute{"s" if minutes > 1 else ""}'

    return output


def notify_discord() -> None:
    """
    Create and submit the Discord notification. This parses the
    Blueprint submission from the environment variables.
    """

    # Verify webhook URL is available
    if 'DISCORD_WEBHOOK' not in environ:
        print(f'DISCORD_WEBHOOK environment variable not provided')
        sys_exit(1)

    # Parse issue from environment variables
    data = parse_submission()

    # Create Embed object for webhook
    embed = DiscordEmbed(
        title=f'New Blueprint for {data["series_name"].strip()} ({data["series_year"]})',
        description='\n'.join(data['blueprint']['description']),
    )

    # Add creator as author
    embed.set_author(
        name=data['creator'],
        icon_url=environ.get('ISSUE_CREATOR_ICON_URL', DEFAULT_AVATAR_URL),
    )

    # Add preview
    embed.set_image(url=data['preview_urls'][0])

    # Add thumbnail if >1 preview
    if len(data['preview_urls']) > 1:
        embed.set_thumbnail(url=data['preview_urls'][1])
    
    # Add fields
    if (templates := len(data['blueprint'].get('templates', []))):
        embed.add_embed_field('Templates', templates)
    if (fonts := len(data['blueprint'].get('fonts', []))):
        embed.add_embed_field('Fonts', fonts)
    if (episodes := len(data['blueprint'].get('episodes', []))):
        embed.add_embed_field('Episodes', episodes)
    if (source_files := len(data['blueprint'].get('series', {}).get('source_files', []))):
        embed.add_embed_field('Source Files', source_files)

    # Add note about availability, add timestamp
    next_str = format_timedelta(get_next_merge_time() - datetime.now())
    embed.set_footer(f'This Blueprint will be available in {next_str}')
    embed.set_timestamp()

    # Create Webhook for adding embeds
    webhook = DiscordWebhook(
        url=environ.get('DISCORD_WEBHOOK'),
        username=environ.get('DISCORD_USERNAME', 'MakerBot'),
        avatar_url=environ.get('DISCORD_AVATAR', DEFAULT_AVATAR_URL)
    )

    # Add embed to Webhook, execute webhook
    webhook.add_embed(embed)
    webhook.execute()


if __name__ == '__main__':
    notify_discord()
