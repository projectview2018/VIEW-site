from django.db import models


class Vehicle(models.Model):
    vehicle_make = models.CharField(max_length=50)
    vehicle_model = models.CharField(max_length=50)
    vehicle_year = models.IntegerField()

    def __str__(self) -> str:
        return f'{self.vehicle_year} {self.vehicle_make} {self.vehicle_model}'


class Scan(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT)
    driver_side_start = models.BooleanField()
    eye_x_ft = models.IntegerField(default=0)
    eye_x_in = models.FloatField(default=0)
    eye_y_ft = models.IntegerField(default=0)
    eye_y_in = models.FloatField(default=0)
    eye_z_ft = models.IntegerField(default=0)
    eye_z_in = models.FloatField(default=0)
    lidar_scan = models.FileField(upload_to='lidar_scans/')

    @property
    def eye_x_m(self) -> float:
        return (self.eye_x_ft * 12 + self.eye_x_in * (-1 if self.eye_x_ft < 0 else 1)) * 0.0254

    @property
    def eye_y_m(self) -> float:
        return (self.eye_y_ft * 12 + self.eye_y_in * (-1 if self.eye_y_ft < 0 else 1)) * 0.0254

    @property
    def eye_z_m(self) -> float:
        return (self.eye_z_ft * 12 + self.eye_z_in * (-1 if self.eye_z_ft < 0 else 1)) * 0.0254
