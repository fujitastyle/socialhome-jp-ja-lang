from enumfields.drf import EnumField
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

from socialhome.content.enums import ContentType
from socialhome.content.models import Content, Tag
from socialhome.enums import Visibility
from socialhome.users.serializers import LimitedProfileSerializer


class ContentSerializer(serializers.ModelSerializer):
    author = LimitedProfileSerializer(read_only=True)
    content_type = EnumField(ContentType, ints_as_names=True, read_only=True)
    user_is_author = SerializerMethodField()
    user_has_shared = SerializerMethodField()
    tags = serializers.SlugRelatedField(many=True, read_only=True, slug_field="name")
    through = SerializerMethodField()
    through_author = SerializerMethodField()
    visibility = EnumField(Visibility, lenient=True, ints_as_names=True, required=False)

    class Meta:
        model = Content
        fields = (
            "author",
            "content_type",
            "edited",
            "uuid",
            "has_twitter_oembed",
            "humanized_timestamp",
            "id",
            "is_nsfw",
            "local",
            "order",
            "parent",
            "pinned",
            "remote_created",
            "rendered",
            "reply_count",
            "root_parent",
            "service_label",
            "share_of",
            "shares_count",
            "tags",
            "text",
            "through",
            "through_author",
            "timestamp",
            "url",
            "user_is_author",
            "user_has_shared",
            "visibility",
        )
        read_only_fields = (
            "author",
            "content_type"
            "edited",
            "uuid",
            "has_twitter_oembed",
            "humanized_timestamp",
            "id",
            "is_nsfw",
            "local",
            "remote_created",
            "rendered",
            "reply_count",
            "root_parent",
            "share_of",
            "shares_count",
            "tags",
            "through",
            "through_author",
            "timestamp",
            "url",
            "user_is_author",
            "user_has_shared",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache_through_authors()

    def cache_through_authors(self):
        """
        If we have 'throughs', cache author information here for all of them.
        """
        request = self.context.get("request")
        if not self.context.get("throughs") or not request:
            self.context["throughs_authors"] = {}
            return
        throughs_ids = self.context["throughs"]
        ids = {value for _key, value in throughs_ids.items()}
        through_to_id = {value: key for key, value in throughs_ids.items()}
        throughs = Content.objects.visible_for_user(request.user).select_related("author").filter(id__in=list(ids))
        self.context["throughs_authors"] = {through_to_id.get(c.id, c.id): c.author for c in throughs}

    def get_through(self, obj):
        """Through is generally required only for serializing content for streams."""
        throughs = self.context.get("throughs")
        if not throughs:
            return obj.id
        return throughs.get(obj.id, obj.id)

    def get_through_author(self, obj):
        throughs_authors = self.context.get("throughs_authors")
        if not throughs_authors:
            return {}
        through_author = throughs_authors.get(obj.id, obj.author)
        if through_author != obj.author:
            return LimitedProfileSerializer(
                instance=through_author,
                read_only=True,
                context={"request": self.context.get("request")},
            ).data
        return {}

    def get_user_is_author(self, obj):
        request = self.context.get("request")
        if not request:
            return False
        return bool(request.user.is_authenticated and obj.author == request.user.profile)

    def get_user_has_shared(self, obj):
        request = self.context.get("request")
        if not request:
            return False
        return Content.has_shared(obj.id, request.user.profile.id) if hasattr(request.user, "profile") else False

    def validate(self, data):
        """
        Validate visibility is not required for replies.

        If given, make sure it is the same as parent. If not given, use parent visibility.
        """
        parent = data.get("parent")
        if parent:
            if data.get("visibility") and parent.visibility != data.get("visibility"):
                raise serializers.ValidationError("Visibility was given but it doesn't match parent.")
            data["visibility"] = parent.visibility
        else:
            if not self.instance and not data.get("visibility"):
                raise serializers.ValidationError("Visibility is required")
        return data

    def validate_parent(self, value):
        # Validate parent cannot be changed
        if self.instance and value != self.instance.parent:
            raise serializers.ValidationError("Parent cannot be changed for an existing Content instance.")
        # Validate user can see parent
        if not self.instance and value:
            request = self.context.get("request")
            if not value.visible_for_user(request.user):
                raise serializers.ValidationError("Parent not found")
        return value

    def validate_visibility(self, value):
        """
        Don't allow creating Limited visibility as of now.
        """
        if value == Visibility.LIMITED and not self.instance:
            raise serializers.ValidationError("Limited content creation not yet supported via the API.")
        return value


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("name", "created", "uuid")
        read_only_fields = ("created", "uuid")
