"""Explicit experiment inputs, shared by projection and scheduling."""
from datetime import date, timedelta
from agents.digitaltwin.services.eligibility import operational_readings, validate_parcel_parameters


async def experiment_inputs(db, parcel, request):
    validate_parcel_parameters(parcel)
    if request.mode == 'demonstration':
        initial = request.initial_moisture_mm
        if initial is None or not 0 <= initial <= parcel.field_capacity_mm:
            raise ValueError('Demonstration mode requires initial moisture between 0 and field capacity.')
        return [], date.today()
    if request.initial_moisture_mm is not None:
        raise ValueError('Field mode uses the reviewed measurement; clear the assumed initial moisture.')
    readings = await operational_readings(db, parcel)
    return readings, max(date.today(), readings[-1].recorded_at.date() + timedelta(days=1))


def experiment_snapshot(parcel, request, readings, forecast):
    return {
        'mode': request.mode,
        'operational_approval_allowed': request.mode == 'field',
        'source_reading_id': readings[-1].id if readings else None,
        'input_provenance': 'Assumed demonstration input' if not readings else 'Reviewed field measurement',
        'request': request.model_dump(mode='json'),
        'initial_moisture_mm': readings[-1].soil_moisture_mm if readings else request.initial_moisture_mm,
        'parcel_snapshot': {key: getattr(parcel, key) for key in ('id', 'name', 'code', 'area_ha', 'latitude', 'longitude', 'crop_type', 'soil_type', 'field_capacity_mm', 'wilting_point_mm')},
        'weather_inputs': [vars(value) for value in forecast.inputs],
        'forecast_coverage_start': forecast.start_date.isoformat(),
        'forecast_coverage_end': forecast.end_date.isoformat(),
        'forecast_provider': forecast.provider,
        'forecast_model': forecast.provider_model,
        'forecast_retrieved_at': forecast.retrieved_at.isoformat(),
    }
