from rest_framework import serializers
from .models import StudentGroup, StudentGroupMembership

# --- GDPR Serializers for Student Group Data ---

class GDPRStudentGroupSerializer(serializers.ModelSerializer):
    """Minimal group info for GDPR export."""
    owner_username = serializers.CharField(source='owner.username', read_only=True)

    class Meta:
        model = StudentGroup
        fields = ('id', 'name', 'owner_username') # Include owner username for context

class GDPRStudentGroupMembershipSerializer(serializers.ModelSerializer):
    """Serializer for student group memberships for GDPR export."""
    group = GDPRStudentGroupSerializer(read_only=True)
    # joined_at: Timestamp when the student joined the group.
    class Meta:
        model = StudentGroupMembership
        fields = ('id', 'group', 'joined_at')