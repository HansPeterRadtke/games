public interface ISaveableEntity
{
    string SaveId { get; }
    SaveEntityData CaptureState();
    void RestoreState(SaveEntityData data);
}
