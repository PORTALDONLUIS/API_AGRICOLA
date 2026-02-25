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

class PlantillaRegistro(models.Model):
    RegistroId = models.BigAutoField(primary_key=True)
    PlantillaId = models.IntegerField()
    UserId = models.IntegerField()
    FechaRegistro = models.DateTimeField()
    FechaEjecucion = models.DateTimeField(null=True, blank=True)
    CampaniaId = models.CharField(max_length=8, null=True, blank=True)
    LoteId = models.IntegerField(null=True, blank=True)
    Lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    Lon = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    Estado = models.CharField(max_length=30)
    DataJson = models.TextField()
    SyncStatus = models.CharField(max_length=30)
    SyncError = models.CharField(max_length=400, null=True, blank=True)
    SyncAttempts = models.IntegerField()
    ServerRegistroId = models.BigIntegerField(null=True, blank=True)
    CreatedAt = models.DateTimeField()
    UpdatedAt = models.DateTimeField()
    DeletedAt = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'dbo.PlantillaRegistro'


class Campania(models.Model):
    id_campania = models.CharField(db_column="ID_CAMPANIA", primary_key=True, max_length=8)
    descripcion = models.CharField(db_column="DESCRIPCION", max_length=50)

    class Meta:
        managed = False
        db_table = "CAMPANIA"


class Lote(models.Model):
    id_lote = models.AutoField(db_column="ID_LOTE", primary_key=True)
    descripcion = models.CharField(db_column="DESCRIPCION", max_length=100)
    area_total = models.DecimalField(db_column="AREA_TOTAL", max_digits=10, decimal_places=2, null=True, blank=True)
    id_fundo = models.CharField(db_column="ID_FUNDO", max_length=15)
    id_variedad = models.BigIntegerField(db_column="ID_VARIEDAD")
    ceco = models.CharField(db_column="CECO", max_length=15)
    geom = models.TextField(db_column="Geom", null=True, blank=True)

    class Meta:
        managed = False
        db_table = "LOTE"
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

class PlantillaRegistro(models.Model):
    RegistroId = models.BigAutoField(primary_key=True)
    PlantillaId = models.IntegerField()
    UserId = models.IntegerField()
    FechaRegistro = models.DateTimeField()
    FechaEjecucion = models.DateTimeField(null=True, blank=True)
    CampaniaId = models.CharField(max_length=8, null=True, blank=True)
    LoteId = models.IntegerField(null=True, blank=True)
    Lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    Lon = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    Estado = models.CharField(max_length=30)
    DataJson = models.TextField()
    SyncStatus = models.CharField(max_length=30)
    SyncError = models.CharField(max_length=400, null=True, blank=True)
    SyncAttempts = models.IntegerField()
    ServerRegistroId = models.BigIntegerField(null=True, blank=True)
    CreatedAt = models.DateTimeField()
    UpdatedAt = models.DateTimeField()
    DeletedAt = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'dbo.PlantillaRegistro'


class Campania(models.Model):
    id_campania = models.CharField(db_column="ID_CAMPANIA", primary_key=True, max_length=8)
    descripcion = models.CharField(db_column="DESCRIPCION", max_length=50)

    class Meta:
        managed = False
        db_table = "CAMPANIA"


class Lote(models.Model):
    id_lote = models.AutoField(db_column="ID_LOTE", primary_key=True)
    descripcion = models.CharField(db_column="DESCRIPCION", max_length=100)
    area_total = models.DecimalField(db_column="AREA_TOTAL", max_digits=10, decimal_places=2, null=True, blank=True)
    id_fundo = models.CharField(db_column="ID_FUNDO", max_length=15)
    id_variedad = models.BigIntegerField(db_column="ID_VARIEDAD")
    ceco = models.CharField(db_column="CECO", max_length=15)

    class Meta:
        managed = False
        db_table = "LOTE"