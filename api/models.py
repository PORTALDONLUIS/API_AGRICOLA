from django.db import models
from django.conf import settings

class Plantilla(models.Model):
    # Mapea PlantillaId -> id (así tu código id__in funciona)
    id = models.AutoField(primary_key=True, db_column="PlantillaId")

    codigo = models.CharField(max_length=50, unique=True, db_column="Codigo")
    nombre = models.CharField(max_length=150, db_column="Nombre")
    descripcion = models.CharField(max_length=400, null=True, blank=True, db_column="Descripcion")

    payload_json = models.TextField(db_column="PayloadJson")
    version = models.IntegerField(db_column="Version")
    is_active = models.BooleanField(db_column="IsActive")

    updated_at = models.DateTimeField(db_column="UpdatedAt")
    deleted_at = models.DateTimeField(null=True, blank=True, db_column="DeletedAt")

    class Meta:
        managed = False
        db_table = "dbo.Plantilla"


class UserPlantilla(models.Model):
    id = models.AutoField(primary_key=True, db_column="UserPlantillaId")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.DO_NOTHING,
        db_column="UserId",
        related_name="plantillas_asignadas"
    )

    plantilla = models.ForeignKey(
        Plantilla,
        on_delete=models.DO_NOTHING,
        db_column="PlantillaId",
        related_name="asignaciones"
    )

    estado = models.CharField(max_length=30, db_column="Estado")
    assigned_at = models.DateTimeField(db_column="AssignedAt")
    updated_at = models.DateTimeField(db_column="UpdatedAt")
    deleted_at = models.DateTimeField(null=True, blank=True, db_column="DeletedAt")

    class Meta:
        managed = False
        db_table = "dbo.UserPlantilla"
        unique_together = (("user", "plantilla"),)
