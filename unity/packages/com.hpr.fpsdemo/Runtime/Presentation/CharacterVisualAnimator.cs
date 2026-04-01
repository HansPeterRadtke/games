using UnityEngine;

namespace HPR
{
    public class CharacterVisualAnimator : MonoBehaviour
    {
        private static readonly int MoveSpeedHash = Animator.StringToHash("MoveSpeed");
        private static readonly int AttackHash = Animator.StringToHash("Attack");
        private static readonly int HitHash = Animator.StringToHash("Hit");
        private static readonly int DeadHash = Animator.StringToHash("Dead");

        [SerializeField] private float moveDamp = 10f;
        [SerializeField] private float deadPitchDegrees = 78f;
        [SerializeField] private float deadSinkOffset = -0.18f;
        [SerializeField] private float deathLerpSpeed = 6f;

        private Animator animator;
        private Transform visualRoot;
        private float targetMoveSpeed;
        private float currentMoveSpeed;
        private bool dead;
        private Quaternion initialLocalRotation;
        private Vector3 initialLocalPosition;
        private Quaternion deadLocalRotation;
        private Vector3 deadLocalPosition;

        private void Awake()
        {
            animator = GetComponentInChildren<Animator>(true);
            visualRoot = animator != null ? animator.transform : transform;
            initialLocalRotation = visualRoot.localRotation;
            initialLocalPosition = visualRoot.localPosition;
            deadLocalRotation = Quaternion.Euler(deadPitchDegrees, 0f, 0f) * initialLocalRotation;
            deadLocalPosition = initialLocalPosition + new Vector3(0f, deadSinkOffset, 0f);
        }

        private void LateUpdate()
        {
            if (animator != null)
            {
                currentMoveSpeed = Mathf.MoveTowards(currentMoveSpeed, targetMoveSpeed, Time.deltaTime * moveDamp);
                animator.SetFloat(MoveSpeedHash, currentMoveSpeed);
                animator.SetBool(DeadHash, dead);
            }

            if (!dead)
            {
                return;
            }

            visualRoot.localRotation = Quaternion.Slerp(visualRoot.localRotation, deadLocalRotation, Time.deltaTime * deathLerpSpeed);
            visualRoot.localPosition = Vector3.Lerp(visualRoot.localPosition, deadLocalPosition, Time.deltaTime * deathLerpSpeed);
        }

        public void SetMoveSpeed(float normalizedSpeed)
        {
            if (dead)
            {
                targetMoveSpeed = 0f;
                return;
            }

            targetMoveSpeed = Mathf.Clamp01(normalizedSpeed);
        }

        public void TriggerAttack()
        {
            if (dead || animator == null)
            {
                return;
            }

            animator.ResetTrigger(HitHash);
            animator.SetTrigger(AttackHash);
        }

        public void TriggerHit()
        {
            if (dead || animator == null)
            {
                return;
            }

            animator.ResetTrigger(AttackHash);
            animator.SetTrigger(HitHash);
        }

        public void TriggerDeath()
        {
            dead = true;
            targetMoveSpeed = 0f;
            currentMoveSpeed = 0f;
            if (animator != null)
            {
                animator.ResetTrigger(AttackHash);
                animator.ResetTrigger(HitHash);
                animator.SetBool(DeadHash, true);
            }
        }

        public void ResetPresentation()
        {
            dead = false;
            targetMoveSpeed = 0f;
            currentMoveSpeed = 0f;
            if (animator != null)
            {
                animator.Rebind();
                animator.Update(0f);
                animator.SetFloat(MoveSpeedHash, 0f);
                animator.SetBool(DeadHash, false);
            }

            visualRoot.localRotation = initialLocalRotation;
            visualRoot.localPosition = initialLocalPosition;
        }
    }
}
