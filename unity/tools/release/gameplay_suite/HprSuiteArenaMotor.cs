// HPR Gameplay Systems Suite — original primitive-arena movement adapter.
using System;
using UnityEngine;

namespace HPR.GameplaySuite
{
    /// <summary>Collision-aware planar sample motor. Not a full third-person controller.</summary>
    [DisallowMultipleComponent]
    public sealed class HprSuiteArenaMotor : MonoBehaviour
    {
        [SerializeField, Min(0f)] private float moveSpeed = 4f;
        [SerializeField] private float gravity = -18f;
        private CharacterController controller;
        private float fallSpeed;

        public bool UsesCharacterController => controller != null && controller.enabled;

        public void SetMoveSpeed(float value)
        {
            if (float.IsNaN(value) || float.IsInfinity(value) || value < 0f)
                throw new ArgumentOutOfRangeException(nameof(value));
            moveSpeed = value;
        }

        private void Awake()
        {
            controller = GetComponent<CharacterController>();
        }

        public void MovePlanar(Vector2 direction, float deltaTime)
        {
            if (deltaTime < 0f || float.IsNaN(deltaTime) || float.IsInfinity(deltaTime))
                throw new ArgumentOutOfRangeException(nameof(deltaTime));
            if (deltaTime <= 0f) return;
            direction = Vector2.ClampMagnitude(direction, 1f);
            Vector3 movement = new Vector3(direction.x, 0f, direction.y) * (moveSpeed * deltaTime);
            if (controller != null && controller.enabled)
            {
                fallSpeed = controller.isGrounded ? -1f : Mathf.Max(-30f, fallSpeed + gravity * deltaTime);
                controller.Move(movement + Vector3.up * fallSpeed * deltaTime);
            }
            else
            {
                // Pure-Unity test scaffolds without CharacterController can exercise the adapter.
                transform.position += movement;
            }
        }

        public void Warp(Vector3 position, Quaternion rotation)
        {
            bool active = controller != null && controller.enabled;
            if (active) controller.enabled = false;
            transform.SetPositionAndRotation(position, rotation);
            if (active) controller.enabled = true;
            fallSpeed = 0f;
        }
    }
}
