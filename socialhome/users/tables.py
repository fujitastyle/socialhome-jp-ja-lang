from django_tables2 import TemplateColumn, LinkColumn, Table
from django_tables2.utils import Accessor

from socialhome.users.models import Profile


class FollowedTable(Table):
    picture = TemplateColumn(template_name="users/_picture_column.html", orderable=False)
    handle = LinkColumn(
        "users:profile-detail", args=[Accessor("uuid")], text=lambda record: record.handle,
        attrs={"th": {"class": "hidden-md-down"}, "td": {"class": "hidden-md-down"}},
    )
    name = LinkColumn("users:profile-detail", args=[Accessor("uuid")], text=lambda record: record.name)
    actions = TemplateColumn(
        template_name="users/_actions_column.html", orderable=False, attrs={"td": {"class": "align-middle"}},
    )

    class Meta:
        model = Profile
        fields = ()
        order_by = ("name", "handle")
        template = "django_tables2/bootstrap.html"
        sequence = ("picture", "name", "handle")
