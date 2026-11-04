<template>
  <span class="nomi-avatar" :class="{ 'is-thinking': thinking, 'is-angry': angry }" aria-hidden="true">
    <svg
      class="puppy"
      viewBox="0 0 1024 1080"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      focusable="false"
    >
      <ellipse class="puppy-shadow" cx="512" cy="1000" rx="350" ry="22" fill="#a76b3e" />

      <g class="puppy-body">
        <g class="puppy-head">
          <!-- Keep the orange-and-white silhouette from the supplied puppy SVG. -->
          <path
            d="M242.834286 54.125714c-115.744183-11.445394-117.920914 223.328549-106.615955 370.866469-56.793966 81.355337-75.71456 176.049006-61.445851 243.182446 28.578377 134.465829 146.516846 199.551269 211.233646 225.947062 106.96704 43.625326 366.074149 85.515703 550.089874-50.904502 122.169051-90.568411 134.632594-309.704411 43.177691-418.225006C900.707474 45.717211 801.821257 44.210469 747.52 58.514286c-38.979291 10.269257-135.033417 121.311817-168.228571 177.005714-47.428754-13.838629-130.60096-11.559497-163.84-5.169737C345.409829 94.006126 261.321874 55.954286 242.834286 54.125714Z"
            fill="#fbaf5e"
            stroke="#7c4000"
            stroke-width="20"
            stroke-linejoin="round"
          />
          <path
            d="M192.213577 376.837851c-21.931154.766537-16.817006-235.262537 54.731337-234.651062 11.761371.886491 102.329783 79.85152 99.497692 102.42048-1.614994 12.873143-36.864 39.292343-75.24352 68.057965-28.888503 21.653211-59.552914 44.634697-78.985509 64.172617ZM819.984091 381.39904c21.928229.766537 16.817006-235.265463-54.731337-234.651063-11.764297.886491-102.329783 79.85152-99.497691 102.417554 1.614994 12.876069 36.864 39.292343 75.24352 68.060892 28.888503 21.653211 59.552914 44.634697 78.985508 64.172617Z"
            fill="#fff8f1"
          />
          <path
            d="M301.348571 560.274286c41.63584 8.76544 62.902857 6.609189 78.994286-2.925715 26.331429-12.67712 55.445211-42.422857 122.88-42.422857 73.142857 0 106.788571 27.794286 128.731429 42.422857 7.753143 5.169737 33.645714 9.210149 57.051428 7.314286 54.125714-4.388571 122.88-98.011429 206.262857-24.868571 31.451429 27.589486 49.236846 161.75104-32.182857 266.24-87.771429 112.642926-276.48 125.805714-345.234285 125.805714-136.115931 0-258.925714-38.034286-311.588572-80.457143S61.053806 677.653943 102.4 588.068571c52.662857-114.102857 171.154286-33.645714 198.948571-27.794285Z"
            fill="#fffdf9"
          />

          <g fill="#fff8f1">
            <circle cx="408" cy="420" r="30" />
            <circle cx="625" cy="420" r="30" />
          </g>
          <g class="puppy-blush" fill="#ff9996">
            <ellipse cx="244" cy="540" rx="57" ry="25" />
            <ellipse cx="780" cy="540" rx="57" ry="25" />
          </g>

          <g class="puppy-alert-eyes">
            <g class="puppy-eyes-open" fill="#5a2f00">
              <g class="puppy-gaze">
                <ellipse cx="350" cy="494" rx="31" ry="40" />
                <ellipse cx="674" cy="494" rx="31" ry="40" />
                <g fill="#fff">
                  <circle cx="341" cy="481" r="10" />
                  <circle cx="665" cy="481" r="10" />
                </g>
              </g>
            </g>
          </g>
          <g class="puppy-eyes-happy" stroke="#5a2f00" stroke-width="25" stroke-linecap="round">
            <path d="M296 503Q350 464 404 498" />
            <path d="M620 498Q674 464 728 503" />
          </g>
          <g class="puppy-brows" stroke="#7c4000" stroke-width="22" stroke-linecap="round">
            <path d="m313 441 78 28" />
            <path d="m635 469 78-28" />
          </g>

          <path
            d="M512.6 639.1c33.6 0 60.85-31.07 60.85-52.73S546.2 553 512.6 553s-60.84 11.7-60.84 33.37 27.24 52.73 60.84 52.73Z"
            fill="#5a2f00"
          />
          <ellipse cx="482" cy="578" rx="13" ry="5" transform="rotate(-18 482 578)" fill="#fff" opacity=".65" />
          <g stroke="#5a2f00" stroke-width="21" stroke-linecap="round" stroke-linejoin="round">
            <path class="puppy-smile" d="M365 668q32 51 83 35 62-21 124 0 51 16 87-35" />
            <path class="puppy-pout" d="M449 714q63-30 126 0" />
          </g>
        </g>

        <g class="puppy-paw-left">
          <path
            d="M199.922834 962.855497c-20.597029 9.710446-61.908114 18.467109-62.405485-24.1664-.6144-53.291886 24.716434-154.299246 132.836205-126.414263 108.122697 27.884983 119.860663 110.922606 114.919132 126.414263-4.944457 15.491657-15.447771 37.179977-50.044343 24.1664-8.443611 20.655543-34.353737 52.302994-70.433646 13.633829-13.797669 12.1856-46.091703 26.5216-64.874788-13.633829Z"
            fill="#fffdf9"
            stroke="#7c4000"
            stroke-width="20"
            stroke-linejoin="round"
          />
        </g>

        <g class="puppy-paw-right">
          <g class="puppy-paw-back">
            <path
              d="M199.922834 962.855497c-20.597029 9.710446-61.908114 18.467109-62.405485-24.1664-.6144-53.291886 24.716434-154.299246 132.836205-126.414263 108.122697 27.884983 119.860663 110.922606 114.919132 126.414263-4.944457 15.491657-15.447771 37.179977-50.044343 24.1664-8.443611 20.655543-34.353737 52.302994-70.433646 13.633829-13.797669 12.1856-46.091703 26.5216-64.874788-13.633829Z"
              transform="translate(1024 0) scale(-1 1)"
              fill="#fffdf9"
              stroke="#7c4000"
              stroke-width="20"
              stroke-linejoin="round"
            />
          </g>
          <g class="puppy-paw-front">
            <path
              d="M702.823863 773.20192c10.19904-10.368731 18.625097-18.941074 46.720731-5.942126 14.283337 6.609189 26.764434 4.613851 38.821303 2.688732 12.053943-1.92512 23.683657-3.782949 36.273006 3.09248 10.102491 5.520823 14.116571 13.563611 18.294491 21.931154 5.18144 10.380434 10.614491 21.267017 28.230217 28.464274 32.592457 13.314926 42.446263 42.130286 37.548618 71.04512-4.897646 28.914834-68.564114 121.440549-174.676846 95.831772-106.112731-25.611703-124.708571-105.071177-114.097006-147.204389 8.21248-32.607086 25.35424-39.514697 46.773394-48.142628 6.255177-2.51904 12.876069-5.187291 19.745646-8.686446 7.027566-3.578149 11.869623-8.502126 16.366446-13.077943Z"
              fill="#fffdf9"
              stroke="#7c4000"
              stroke-width="20"
              stroke-linejoin="round"
            />
            <g fill="#ff9996">
              <circle cx="707" cy="829" r="19" />
              <circle cx="780" cy="838" r="19" />
              <circle cx="859" cy="876" r="19" />
              <ellipse cx="754" cy="918" rx="73" ry="44" transform="rotate(14 754 918)" />
            </g>
          </g>
        </g>

        <!-- Follow the head's pose, but keep the tongue in front of the raised paw. -->
        <g class="puppy-tongue-pose">
          <g class="puppy-tongue">
            <path
              d="M550 698c31 4 86 30 108 51 19 19-3 43-24 29l-73-51Z"
              fill="#f48e9c"
              stroke="#9a5140"
              stroke-width="12"
              stroke-linejoin="round"
            />
            <path d="m576 714 54 42" stroke="#d96b80" stroke-width="9" stroke-linecap="round" />
          </g>
        </g>
      </g>
    </svg>
  </span>
</template>

<script setup>
defineProps({
  thinking: Boolean,
  angry: Boolean
})
</script>

<style scoped>
.nomi-avatar {
  --puppy-cycle: 12s;
  display: inline-block;
  width: 100%;
  height: 100%;
  line-height: 0;
  vertical-align: middle;
}

.puppy {
  display: block;
  width: 100%;
  height: 100%;
  overflow: visible;
  pointer-events: none;
}

.puppy g,
.puppy-shadow {
  transform-box: view-box;
}

.puppy-shadow {
  opacity: .16;
  transform-origin: 512px 1000px;
  animation: puppy-shadow 3.6s ease-in-out infinite;
}

.puppy-body {
  transform-origin: 512px 970px;
  animation: puppy-breathe 3.6s ease-in-out infinite;
}

.puppy-head,
.puppy-tongue-pose {
  transform-origin: 512px 760px;
  animation: puppy-look-around var(--puppy-cycle) ease-in-out infinite;
}

.puppy-alert-eyes {
  animation: puppy-alert-eyes var(--puppy-cycle) ease-in-out infinite;
}

.puppy-eyes-open {
  transform-origin: 512px 494px;
  animation: puppy-blink 4.6s ease-in-out infinite;
}

.puppy-eyes-happy {
  opacity: 0;
  animation: puppy-happy-eyes var(--puppy-cycle) ease-in-out infinite;
}

.puppy-brows,
.puppy-pout {
  opacity: 0;
}

.puppy-blush {
  opacity: .85;
}

.puppy-tongue {
  opacity: 0;
  transform: scale(0);
  transform-origin: 550px 698px;
  animation: puppy-lick var(--puppy-cycle) ease-in-out infinite;
}

.puppy-paw-left {
  transform-origin: 264px 945px;
  animation: puppy-tuck var(--puppy-cycle) ease-in-out infinite;
}

.puppy-paw-right {
  transform-origin: 760px 900px;
  animation: puppy-lift-paw var(--puppy-cycle) ease-in-out infinite;
}

.puppy-paw-back {
  opacity: 1;
}

.puppy-paw-front {
  opacity: 0;
}

.nomi-avatar:is(.is-thinking, .is-angry) .puppy-tongue {
  opacity: 0;
  animation: none;
}

.nomi-avatar:is(.is-thinking, .is-angry) .puppy-alert-eyes {
  opacity: 1;
  animation: none;
}

.nomi-avatar:is(.is-thinking, .is-angry) .puppy-eyes-happy {
  opacity: 0;
  animation: none;
}

.nomi-avatar:is(.is-thinking, .is-angry) .puppy-paw-left {
  animation: none;
}

.nomi-avatar.is-thinking .puppy-head {
  transform: rotate(-8deg);
  animation: puppy-think 2.8s ease-in-out infinite;
}

.nomi-avatar.is-thinking .puppy-gaze {
  transform: translate(9px, -8px);
}

.nomi-avatar.is-thinking .puppy-paw-right {
  transform: translate(-95px, -75px) rotate(60deg) scale(.86, .84);
  animation: puppy-chin-paw 2.8s ease-in-out infinite;
}

.nomi-avatar.is-angry .puppy-head {
  transform: translateY(12px);
  animation: puppy-huff .45s ease-in-out 2;
}

.nomi-avatar.is-angry .puppy-brows,
.nomi-avatar.is-angry .puppy-pout {
  opacity: 1;
}

.nomi-avatar.is-angry .puppy-smile {
  opacity: 0;
}

.nomi-avatar.is-angry .puppy-gaze {
  transform: translateY(6px) scaleY(.98);
}

.nomi-avatar.is-angry .puppy-paw-right {
  transform: translate(10px, 12px) rotate(8deg);
  animation: none;
}

@media (hover: hover) {
  .nomi-avatar:not(.is-thinking):not(.is-angry):hover .puppy-head {
    animation: none;
    transform: translateY(-14px) rotate(-5deg);
  }

  .nomi-avatar:not(.is-thinking):not(.is-angry):hover .puppy-paw-right {
    animation: puppy-wave .85s ease-in-out infinite;
  }

  .nomi-avatar:not(.is-thinking):not(.is-angry):hover .puppy-paw-back {
    opacity: 0;
  }

  .nomi-avatar:not(.is-thinking):not(.is-angry):hover .puppy-paw-front {
    opacity: 1;
  }

  .nomi-avatar:not(.is-thinking):not(.is-angry):hover .puppy-alert-eyes {
    opacity: 0;
    animation: none;
  }

  .nomi-avatar:not(.is-thinking):not(.is-angry):hover .puppy-eyes-happy {
    opacity: 1;
    animation: none;
  }

  .nomi-avatar:hover .puppy-tongue {
    opacity: 0;
    animation: none;
  }
}

@keyframes puppy-breathe {
  0%, 100% { transform: translateY(0) scale(1); }
  50% { transform: translateY(-9px) scale(1.008, 1.012); }
}

@keyframes puppy-shadow {
  0%, 100% { transform: scaleX(1); opacity: .16; }
  50% { transform: scaleX(.94); opacity: .12; }
}

@keyframes puppy-look-around {
  0%, 6%, 18%, 36%, 74%, 100% { transform: translate(0, 0) rotate(0); }
  10%, 13% { transform: translate(-6px, -5px) rotate(-4deg); }
  27%, 30% { transform: translate(4px, 0) rotate(3deg); }
  45% { transform: translate(14px, 28px) rotate(4deg); }
  49%, 64% { transform: translate(24px, 58px) rotate(7deg); }
  68% { transform: translate(10px, 24px) rotate(3deg); }
}

@keyframes puppy-blink {
  0%, 40%, 46%, 72%, 78%, 100% { transform: scaleY(1); }
  43%, 75% { transform: scaleY(.06); }
}

@keyframes puppy-alert-eyes {
  0%, 41%, 72%, 100% { opacity: 1; }
  45%, 68% { opacity: 0; }
}

@keyframes puppy-happy-eyes {
  0%, 41%, 72%, 100% { opacity: 0; }
  45%, 68% { opacity: 1; }
}

@keyframes puppy-tuck {
  0%, 17%, 34%, 100% { transform: translate(0, 0) scale(1); }
  23%, 28% { transform: translate(12px, 18px) scale(.84, .82); }
}

@keyframes puppy-lift-paw {
  0%, 39%, 74%, 100% { transform: translate(0, 0) rotate(0) scale(1); }
  47%, 51%, 56%, 61%, 65% { transform: translate(-45px, -85px) rotate(70deg) scale(.84, .82); }
  53%, 58%, 63% { transform: translate(-49px, -91px) rotate(74deg) scale(.82, .8); }
}

@keyframes puppy-lick {
  0%, 48%, 53%, 58%, 63%, 100% { opacity: 0; transform: scale(.1); }
  50%, 55%, 60% { opacity: 1; transform: scale(1); }
}

@keyframes puppy-wave {
  0%, 100% { transform: translate(-12px, -88px) rotate(-14deg); }
  50% { transform: translate(2px, -105px) rotate(8deg); }
}

@keyframes puppy-think {
  0%, 100% { transform: translate(0, -8px) rotate(-8deg); }
  50% { transform: translate(8px, 0) rotate(3deg); }
}

@keyframes puppy-chin-paw {
  0%, 100% { transform: translate(-95px, -75px) rotate(60deg) scale(.86, .84); }
  50% { transform: translate(-87px, -69px) rotate(54deg) scale(.86, .84); }
}

@keyframes puppy-huff {
  0%, 100% { transform: translate(0, 12px) rotate(0); }
  25% { transform: translate(-12px, 12px) rotate(-3deg); }
  75% { transform: translate(12px, 12px) rotate(3deg); }
}

@media (prefers-reduced-motion: reduce) {
  .nomi-avatar .puppy g,
  .nomi-avatar .puppy-shadow {
    animation: none !important;
  }
}
</style>
