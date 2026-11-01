// Private Unity Input System Play Mode tests. Not included in the Asset Store package.
// InputTestFixture is the official Unity-supported way to simulate devices without
// relying on Unity Editor focus, background input or physical hardware.
#if ENABLE_INPUT_SYSTEM
using NUnit.Framework;
using UnityEngine;
using UnityEngine.InputSystem;
using HPR.GameplaySuite;

namespace HPR.InputQA.Tests
{
    public sealed class HprSuiteInputPlayModeFixtureTests : InputTestFixture
    {
        [Test]
        public void NewInputOnly_LetterPressAndReleasePreserveJustPressedTransition()
        {
            Keyboard keyboard = InputSystem.AddDevice<Keyboard>();
            var source = HprSuiteUnityInputSource.Instance;

            Assert.That(source.IsPressed(KeyCode.W), Is.False);
            Assert.That(source.WasPressed(KeyCode.W), Is.False);
            Press(keyboard.wKey);
            Assert.That(source.IsPressed(KeyCode.W), Is.True, "Pressed key was not visible.");
            Assert.That(source.WasPressed(KeyCode.W), Is.True,
                "The first simulated dynamic input update must mark a new key press.");

            InputSystem.Update(); // Advance to another input update with W still held.
            Assert.That(source.IsPressed(KeyCode.W), Is.True);
            Assert.That(source.WasPressed(KeyCode.W), Is.False,
                "Holding a key cannot trigger a second just-pressed event.");

            Release(keyboard.wKey);
            Assert.That(source.IsPressed(KeyCode.W), Is.False);
            Assert.That(source.WasPressed(KeyCode.W), Is.False);
        }

        [Test]
        public void NewInputOnly_ModifiersKeypadAndArrowKeysUseCorrectUnityKeyMappings()
        {
            Keyboard keyboard = InputSystem.AddDevice<Keyboard>();
            var source = HprSuiteUnityInputSource.Instance;

            Press(keyboard.leftCtrlKey);
            Press(keyboard.numpad1Key);
            Press(keyboard.leftArrowKey);
            Press(keyboard.digit1Key);

            Assert.That(source.IsPressed(KeyCode.LeftControl), Is.True);
            Assert.That(source.IsPressed(KeyCode.Keypad1), Is.True);
            Assert.That(source.IsPressed(KeyCode.LeftArrow), Is.True);
            Assert.That(source.IsPressed(KeyCode.Alpha1), Is.True);

            Assert.That(source.IsPressed(KeyCode.W), Is.False);
            Assert.That(source.IsPressed(KeyCode.Space), Is.False);
            Assert.That(source.WasPressed(KeyCode.RightControl), Is.False);
        }

        [Test]
        public void NewInputOnly_MousePositionIsReadFromAnIsolatedVirtualPointer()
        {
            var source = HprSuiteUnityInputSource.Instance;
            Assert.That(source.TryGetPointer(out _), Is.False,
                "The test fixture should begin with no mouse device.");

            Mouse mouse = InputSystem.AddDevice<Mouse>();
            Set(mouse.position, new Vector2(320f, 180f));
            Assert.That(source.TryGetPointer(out Vector2 pointer), Is.True);
            Assert.That(pointer.x, Is.EqualTo(320f).Within(0.01f));
            Assert.That(pointer.y, Is.EqualTo(180f).Within(0.01f));
        }
    }
}
#endif
