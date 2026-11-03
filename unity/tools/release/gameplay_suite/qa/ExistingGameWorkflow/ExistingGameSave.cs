// Private customer save seam, authored independently of HPR.
using System;
using System.IO;
using UnityEngine;
namespace ExistingGameWorkflow
{
    public static class ExistingGameSave
    {
        [Serializable] public sealed class State
        {
            public int schema = 1;
            public float health;
            public float stamina;
            public string optionalExtension;
        }
        public static void SaveNew(string path, ExistingGameVitals source, string extension)
        {
            if (source == null) throw new ArgumentNullException(nameof(source));
            if (File.Exists(path)) throw new IOException("Refusing to overwrite customer save");
            string json = JsonUtility.ToJson(new State { health = source.Health, stamina = source.Stamina, optionalExtension = extension });
            using (var stream = new FileStream(path, FileMode.CreateNew, FileAccess.Write))
            using (var writer = new StreamWriter(stream)) writer.Write(json);
        }
        public static string Load(string path, ExistingGameVitals destination)
        {
            if (destination == null) throw new ArgumentNullException(nameof(destination));
            var state = JsonUtility.FromJson<State>(File.ReadAllText(path));
            if (state == null || state.schema != 1) throw new InvalidDataException("Unsupported customer save");
            destination.Restore(state.health, state.stamina);
            return state.optionalExtension;
        }
    }
}
