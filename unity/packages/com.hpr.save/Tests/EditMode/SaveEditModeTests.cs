using NUnit.Framework;
using UnityEngine;

namespace HPR
{
    public class SaveEditModeTests
    {
        [Test]
        public void SerializableVector3_RoundTripsValues()
        {
            Vector3 value = new Vector3(1.5f, -2f, 9f);
            var serializable = new SerializableVector3(value);

            Assert.That(serializable.ToVector3(), Is.EqualTo(value));
        }

        [Test]
        public void SerializableQuaternion_RoundTripsValues()
        {
            Quaternion value = Quaternion.Euler(10f, 25f, -32f);
            var serializable = new SerializableQuaternion(value);

            Assert.That(serializable.ToQuaternion(), Is.EqualTo(value));
        }
    }
}
