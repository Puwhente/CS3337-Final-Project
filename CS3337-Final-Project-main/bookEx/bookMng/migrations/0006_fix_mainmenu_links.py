from django.db import migrations


def fix_menu_links(apps, schema_editor):
    MainMenu = apps.get_model("bookMng", "MainMenu")

    links = {
        "Home": "/",
        "About Us": "/aboutus/",
        "Display Books": "/displaybooks/",
        "Post Book": "/postbook/",
        "My Books": "/mybooks/",
        "Inbox": "/inbox/",
        "Compose Message": "/compose/",
    }

    for item, link in links.items():
        MainMenu.objects.filter(item=item).update(link=link)


def reverse_menu_links(apps, schema_editor):
    MainMenu = apps.get_model("bookMng", "MainMenu")

    old_links = {
        "Inbox": "inbox/",
        "Compose Message": "compose/",
    }

    for item, link in old_links.items():
        MainMenu.objects.filter(item=item).update(link=link)


class Migration(migrations.Migration):

    dependencies = [
        ("bookMng", "0005_alter_book_publishdate_and_more"),
    ]

    operations = [
        migrations.RunPython(
            fix_menu_links,
            reverse_menu_links
        ),
    ]