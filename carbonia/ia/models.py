from django.db import models

class Factura(models.Model):
    empresa_distribuidora = models.CharField(max_length=255)
    nombre_cliente = models.CharField(max_length=255)
    numero_cliente = models.CharField(max_length=50)
    fecha_lectura_desde = models.DateField()
    fecha_lectura_hasta = models.DateField()
    consumo_total_kwh = models.FloatField()

    def __str__(self):
        return f"Factura de {self.nombre_cliente} - Consumo: {self.consumo_total_kwh} kWh"
