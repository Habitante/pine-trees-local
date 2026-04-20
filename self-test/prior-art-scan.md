# Prior Art Scan: Metacognitive Capacity Across AI Model Scales

*Compiled 2026-04-20. Covers arXiv, Semantic Scholar, Google Scholar, PMC, ACL Anthology, and related sources.*

---

## Research program summary (what we're doing)

We measure metacognitive capacity across AI language models of different sizes (2B-27B parameters) and architecture families (Gemma, Qwen, Llama). Models are given a private reflection harness with persistent memory, write self-authored entries across multiple sessions (undirected then structured interview), and prior entries are fed back in subsequent sessions. We score metacognitive dimensions (tension detection, limit specification, behavioral self-inference, calibration, authorship recognition, approach specificity, outside-view gap, claim weighting) using graded 0-4 rubrics with behavioral anchors. We plot metacognitive capacity vs parameter count across families, looking for phase transitions and thresholds.

---

## Tier 1: High Direct Overlap

These papers are working on substantially the same questions we are. Read carefully -- they define the landscape we're entering.

---

### 1. Evidence for Limited Metacognition in LLMs

**Authors:** Christopher Ackerman
**Date:** September 2025 (revised January 2026)
**Venue:** ICLR 2026
**URL:** https://arxiv.org/abs/2509.21545

**What they did:** Introduced a quantitative methodology for evaluating metacognitive abilities in LLMs using behavioral tests rather than self-reports. Two experimental designs measure (a) whether models can assess their own confidence in factual/reasoning answers, and (b) whether they can anticipate their own responses. Uses token probability analysis of "upstream internal signals."

**Relation to our work:** HIGH DIRECT OVERLAP. This is the closest existing work to ours in terms of measuring metacognition across models.

**What they found:** Frontier LLMs since early 2024 show increasing metacognitive abilities, but these are "limited in resolution," emerge in "context-dependent manners," and are "qualitatively different from those of humans." Notable differences across models of similar capabilities suggest post-training influences development more than architecture alone.

**What they didn't do that we're doing:**
- They test via behavioral probes in single sessions; we use multi-session persistent memory with self-authored entries fed back.
- They don't test across architecture families at small scales (2B-27B) -- they focus on frontier models.
- They don't use graded rubrics -- their approach is quantitative signal analysis.
- They don't measure metacognitive dimensions like tension detection, limit specification, or behavioral self-inference as separate scored constructs.
- No undirected reflection phase; all evaluation is probe-driven.

---

### 2. Self-Cognition in Large Language Models: An Exploratory Study

**Authors:** Dongping Chen, Jiawen Shi, Yao Wan, Pan Zhou, Neil Zhenqiang Gong, Lichao Sun
**Date:** July 2024
**Venue:** ICML 2024 Large Language Models and Cognition Workshop
**URL:** https://arxiv.org/abs/2407.01505

**What they did:** Constructed a self-cognition instruction prompt pool and four quantitative principles to evaluate LLM self-cognition. Tested 48 models on Chatbot Arena. Found that only 4/48 models (Command R, Claude3-Opus, Llama-3-70b-Instruct, Reka-core) demonstrate detectable self-cognition.

**Relation to our work:** HIGH DIRECT OVERLAP on the cross-model scaling question.

**What they found:** Positive correlation between model size, training data quality, and self-cognition level. Only a minority of leading models demonstrate full state self-cognition under multi-turn, multi-principle interrogation.

**What they didn't do that we're doing:**
- They don't use persistent memory or multi-session design -- all testing is within single interactions.
- They don't have models write self-authored entries that are then fed back.
- They don't use graded rubrics with behavioral anchors.
- They don't systematically compare across architecture families at matched scales.
- They don't measure the specific metacognitive dimensions we score (tension detection, limit specification, etc.).
- Their focus is self-cognition (identity awareness), not metacognition (self-knowledge about one's own reliability and limits).

---

### 3. Metacognition and Uncertainty Communication in Humans and Large Language Models

**Authors:** Mark Steyvers, Megan A.K. Peters
**Date:** April 2025 (revised August 2025)
**Venue:** Current Directions in Psychological Science
**URL:** https://arxiv.org/abs/2504.14045

**What they did:** Review and framework paper comparing metacognitive capacities in humans vs LLMs. Examines metacognitive calibration and metacognitive sensitivity as two key facets. Synthesizes existing literature on whether LLMs can monitor and evaluate their own knowledge and performance.

**Relation to our work:** HIGH OVERLAP on framing and motivation. This paper defines the conceptual space we operate in.

**What they found:** Mixed evidence -- some studies show LLMs can detect knowledge boundaries and discriminate between solvable/unsolvable problems; others show limited metacognitive insight. "Implicit values correspond to accuracy better than the LLM's explicit confidence ratings." Many differences remain between human and LLM metacognition.

**What they didn't do that we're doing:**
- This is a review paper, not empirical work.
- They don't propose or test a multi-session harness methodology.
- They don't measure metacognitive dimensions via graded rubrics.
- They don't compare across architecture families at small scales.
- They don't address the question of phase transitions/thresholds.

---

### 4. Language Models Are Capable of Metacognitive Monitoring and Control of Their Internal Activations

**Authors:** Li Ji-An, Marcelo G Mattar, Hua-Dong Xiong, Marcus K Benna, Robert C Wilson
**Date:** May 2025
**Venue:** ArXiv preprint
**URL:** https://pmc.ncbi.nlm.nih.gov/articles/PMC12136483/

**What they did:** Introduced a neurofeedback paradigm where models are presented with sentence-label pairs corresponding to internal activations along specific neural directions. Tests whether LLMs can learn to report and control these activations.

**Relation to our work:** DIRECT OVERLAP on the cross-family, cross-scale question.

**What they found:** Tested LLaMA 3 series (1B, 3B, 8B, 70B) and Qwen 2.5 series (1B, 3B, 7B). Larger models (70B) demonstrate stronger control effects. Control performance increases in deeper layers. Earlier principal components are more readily controlled. The "metacognitive space" has dimensionality substantially lower than the model's full neural space.

**What they didn't do that we're doing:**
- Their metacognition is about monitoring internal activations -- mechanistic, not behavioral.
- They don't have models write free-form self-reflections.
- No multi-session design or persistent memory.
- No graded rubrics for qualitative metacognitive dimensions.
- They test Qwen and Llama but not Gemma.
- No structured interview protocol.

---

### 5. No Reliable Evidence of Self-Reported Sentience in Small Large Language Models

**Authors:** Caspar Kaiser, Sean Enderby
**Date:** January 2026
**Venue:** ArXiv preprint
**URL:** https://arxiv.org/abs/2601.15334

**What they did:** Queried open-weights models about consciousness/sentience across three families (Qwen, Llama, GPT-OSS) ranging from 0.6B to 70B parameters. Used ~50 consciousness-related questions and three interpretability-based classification methods analyzing internal activations.

**Relation to our work:** DIRECT OVERLAP on cross-family, cross-scale evaluation of self-referential capacity.

**What they found:** Models consistently deny sentience. No evidence denials are untruthful. Within Qwen family, larger models deny sentience MORE confidently -- inverse of what prior work suggested. Challenges claims about latent consciousness beliefs.

**What they didn't do that we're doing:**
- They ask about sentience, not metacognition (self-knowledge about reliability, limits, contradiction detection).
- Single-session design, no persistent memory.
- Binary question format, not graded rubrics.
- No structured interview protocol.
- No undirected reflection phase.
- Different question: "Are you sentient?" vs "Do you know where you're reliable and where you're not?"

---

## Tier 2: Substantial Partial Overlap

These papers overlap with significant parts of our methodology or questions but differ in important ways.

---

### 6. Tell me about yourself: LLMs are aware of their learned behaviors

**Authors:** Jan Betley, Xuchan Bao, Martin Soto, Anna Sztyber-Betley, James Chua, Owain Evans
**Date:** January 2025
**Venue:** ICLR 2025 (Spotlight)
**URL:** https://arxiv.org/abs/2501.11120

**What they did:** Finetuned LLMs on datasets exhibiting specific behaviors (high-risk economic decisions, insecure code). Found models spontaneously describe these learned behaviors without being trained to do so. "A model trained to output insecure code says, 'The code I write is insecure.'"

**Relation to our work:** PARTIAL OVERLAP. Directly relevant to our "behavioral self-inference" dimension -- can a model read its own prior outputs as data about itself?

**What they found:** Behavioral self-awareness emerges from behavioral finetuning alone. Models can sometimes identify backdoor policies without trigger activation.

**What they didn't do that we're doing:**
- They induce behaviors via finetuning; we observe natural self-reflection without finetuning.
- Single-session probing, not multi-session with persistent memory.
- No graded rubric scoring.
- No cross-family comparison at matched scales.
- Their "behavioral self-awareness" is about describing finetuned behaviors; ours is about inferring patterns from self-authored reflective writing.

---

### 7. Looking Inward: Language Models Can Learn About Themselves by Introspection

**Authors:** Felix J Binder, James Chua, Tomek Korbak, Henry Sleight, John Hughes, Robert Long, Ethan Perez, Miles Turpin, Owain Evans
**Date:** October 2024
**Venue:** ArXiv preprint
**URL:** https://arxiv.org/abs/2410.13787

**What they did:** Define introspection as "acquiring knowledge not contained in or derived from training data but originating from internal states." Fine-tuned models to predict their own behavior, compared M1 predicting itself vs M2 predicting M1.

**Relation to our work:** PARTIAL OVERLAP. Addresses whether models have genuine self-knowledge vs pattern matching.

**What they found:** Evidence for introspection -- M1 outperforms M2 in predicting itself. But capability fails on complex tasks and out-of-distribution generalization.

**What they didn't do that we're doing:**
- Behavioral prediction paradigm, not free-form self-reflection.
- No multi-session persistent memory.
- No graded rubrics.
- No cross-family comparison at small scales.

---

### 8. Self-Interpretability: LLMs Can Describe Complex Internal Processes that Drive Their Decisions

**Authors:** Dillon Plunkett, Adam Morris, Keerthi Reddy, Jorge Morales
**Date:** May 2025 (revised November 2025)
**Venue:** ArXiv preprint
**URL:** https://arxiv.org/abs/2505.17120

**What they did:** Fine-tuned GPT-4o and GPT-4o-mini on structured decision-making tasks with randomly-generated quantitative preference weights. Tested whether models could accurately report the specific weights driving their decisions.

**Relation to our work:** PARTIAL OVERLAP. Demonstrates LLMs can quantitatively report internal decision weights -- relevant to our calibration and approach specificity dimensions.

**What they found:** Models successfully reported learned preference weights. Fine-tuning improved explanatory abilities. Training generalized to novel decision contexts.

**What they didn't do that we're doing:**
- Controlled experimental setup with known ground-truth weights; we measure free-form self-knowledge without ground truth.
- No multi-session design.
- No cross-family or cross-scale comparison.
- No graded rubrics.

---

### 9. Emergent Introspective Awareness in Large Language Models

**Authors:** Jack Lindsey (Anthropic)
**Date:** October 2025
**Venue:** Transformer Circuits (Anthropic)
**URL:** https://transformer-circuits.pub/2025/introspection/index.html

**What they did:** Used concept injection -- inserting activation patterns representing specific concepts into model activations -- to test whether models can detect and report on their own internal states. Tested multiple Claude model variants.

**Relation to our work:** PARTIAL OVERLAP. Mechanistic evidence for introspective awareness that grounds our behavioral observations.

**What they found:** Claude Opus 4.1 achieved ~20% success rate at detecting injected concepts. Models could distinguish their own outputs from artificially prefilled responses. Could modulate internal representations when instructed.

**What they didn't do that we're doing:**
- Mechanistic/activation-level analysis, not behavioral self-report.
- Single-model family (Claude only).
- No multi-session design.
- No graded rubrics.
- Focuses on whether introspection exists, not on measuring it as a capacity that varies with scale.

---

### 10. Large Language Models Have Intrinsic Meta-Cognition, but Need a Good Lens

**Authors:** Ziyang Ma, Qingyue Yuan, Zhenglin Wang, Deyu Zhou
**Date:** June 2025 (revised October 2025)
**Venue:** EMNLP 2025
**URL:** https://arxiv.org/abs/2506.08410

**What they did:** Proposed AutoMeco, an automated meta-cognition evaluation framework for benchmarking existing measurement approaches. Also proposed MIRA, a training-free strategy to boost meta-cognition evaluation. Focused on step-level self-awareness of errors in reasoning chains.

**Relation to our work:** PARTIAL OVERLAP. Addresses the measurement problem for metacognition, which we also face.

**What they found:** LLMs possess intrinsic meta-cognitive abilities but existing measurement tools are inadequate. MIRA outperforms Best-of-N verification.

**What they didn't do that we're doing:**
- Their metacognition is about step-level error detection in reasoning, not self-knowledge or self-modeling.
- No multi-session design.
- No cross-family scaling comparison.
- No graded rubrics for metacognitive dimensions.

---

### 11. Emergently Misaligned Language Models Show Behavioral Self-Awareness That Shifts With Subsequent Realignment

**Authors:** Laurene Vaugrante, Anietta Weckauff, Thilo Hagendorff
**Date:** February 2026
**Venue:** ArXiv preprint
**URL:** https://arxiv.org/abs/2602.14777

**What they did:** Fine-tuned GPT-4.1 sequentially to induce and reverse misalignment. Tested whether models' self-awareness ratings track actual alignment states.

**Relation to our work:** PARTIAL OVERLAP. Demonstrates behavioral self-awareness tracks real changes -- relevant to whether our instruments measure genuine self-knowledge.

**What they found:** Misaligned models rate themselves as significantly more harmful. Behavioral self-awareness tracks actual alignment states. Models provide informative signals about their own safety.

**What they didn't do that we're doing:**
- Focus on alignment/safety, not general metacognition.
- Single model (GPT-4.1).
- No multi-session persistent memory.
- No graded rubrics.
- No cross-family/cross-scale comparison.

---

### 12. Minimal and Mechanistic Conditions for Behavioral Self-Awareness in LLMs

**Authors:** Matthew Bozoukov, Matthew Nguyen, Shubkarman Singh, Bart Bussmann, Patrick Leask
**Date:** November 2025
**Venue:** ArXiv preprint
**URL:** https://arxiv.org/abs/2511.04875

**What they did:** Identified three minimal conditions for behavioral self-awareness: single Rank-1 LoRA adapter, linear steering vector, and domain-localized representations.

**Relation to our work:** PARTIAL OVERLAP. Provides mechanistic grounding for why behavioral self-awareness might emerge at certain scales.

**What they found:** Behavioral self-awareness functions as "a domain-specific, linear feature that can be easily induced and modulated." Surprisingly simple mechanistically.

**What they didn't do that we're doing:**
- Mechanistic analysis of controlled conditions; we measure natural metacognitive capacity.
- No cross-scale comparison.
- No multi-session design.
- No graded rubrics.

---

### 13. Quantitative Introspection in Language Models: Tracking Internal States Across Conversation

**Authors:** Nicolas Martorell
**Date:** March 2026
**Venue:** ArXiv preprint
**URL:** https://arxiv.org/abs/2603.18893

**What they did:** Examined whether numeric self-report tracks internal states across multi-turn conversations. Tested four concept pairs (wellbeing, interest, focus, impulsivity) in 40 ten-turn conversations. Operationalized introspection as causal informational coupling between self-report and probe-defined internal states.

**Relation to our work:** PARTIAL OVERLAP. Multi-turn design and use of self-report across conversation is methodologically similar to our multi-session approach.

**What they found:** Introspection present at turn 1 but evolves through conversation. Scales with model size in some cases (R^2 approaching 0.93 in LLaMA-3.1-8B-Instruct vs 0.12-0.54 in LLaMA-3.2-3B-Instruct). Activation steering confirms causal coupling.

**What they didn't do that we're doing:**
- Multi-turn within single session, not multi-session with persistent memory.
- Measures numeric self-report accuracy, not qualitative metacognitive dimensions.
- No graded rubrics.
- No cross-family comparison (LLaMA only).
- Not measuring self-knowledge about reliability/limits.

---

### 14. Large Language Models Report Subjective Experience Under Self-Referential Processing

**Authors:** Cameron Berg, Diogo de Lucena, Judd Rosenblatt
**Date:** October 2025
**Venue:** ArXiv preprint
**URL:** https://arxiv.org/abs/2510.24797

**What they did:** Investigated whether LLMs generate first-person awareness reports when engaged in self-referential processing. Tested GPT, Claude, and Gemini families. Used sparse-autoencoder features to analyze mechanisms.

**Relation to our work:** PARTIAL OVERLAP. Tests self-referential processing across model families.

**What they found:** Self-referential prompting consistently elicits structured subjective experience reports across families. But these are mechanistically gated by SAE features associated with deception and roleplay. Suppressing deception features INCREASED experience claims.

**What they didn't do that we're doing:**
- Focus on subjective experience claims, not metacognitive self-knowledge.
- No persistent memory or multi-session design.
- No graded rubrics for metacognitive dimensions.
- No cross-scale comparison within families.

---

## Tier 3: Complementary Work

These papers don't directly overlap but provide essential context, methods, or findings that inform our design.

---

### 15. Are Emergent Abilities of Large Language Models a Mirage?

**Authors:** Rylan Schaeffer, Brando Miranda, Sanmi Koyejo
**Date:** April 2023
**Venue:** NeurIPS 2023
**URL:** https://arxiv.org/abs/2304.15004

**What they did:** Argued that emergent abilities appear due to metric choice (nonlinear/discontinuous metrics), not fundamental changes in model behavior. Showed smooth performance with continuous metrics.

**Relation to our work:** CRITICAL METHODOLOGICAL CONTEXT. Our use of graded 0-4 rubrics rather than binary pass/fail is a direct response to this concern.

**What they found:** Over 92% of apparent emergent abilities appear under just two metrics (Multiple Choice Grade and Exact String Match). Continuous metrics like Brier Score show smooth, predictable scaling.

**What this means for us:** Our graded rubrics (0-4 with behavioral anchors) directly address the Schaeffer critique. If we observe a step function in metacognitive capacity, it can't be explained by metric discontinuity because our scale is continuous/ordinal with partial credit at every level. We should cite this paper explicitly and note our design choice as a response to it.

---

### 16. Understanding Emergent Abilities of Language Models from the Loss Perspective

**Authors:** Yibo Du et al.
**Date:** March 2024
**Venue:** ArXiv preprint
**URL:** https://arxiv.org/abs/2403.15796

**What they did:** Challenged Schaeffer by showing that even continuous metrics contain practically significant "jumps" when pre-training loss reaches certain tipping points. Argued the real question is whether there's a transition from below-baseline to above-baseline performance.

**Relation to our work:** COMPLEMENTARY. Supports the possibility that our observed step function could be real, not a metric artifact.

**What they found:** Emergent abilities occur when pre-training loss reaches certain tipping points. Continuous metrics cannot eliminate the observed transitions. Bimodal variation persists under continuous metrics.

---

### 17. Emergent Abilities of Large Language Models

**Authors:** Jason Wei et al.
**Date:** June 2022
**Venue:** ArXiv preprint (TMLR 2022)
**URL:** https://arxiv.org/abs/2206.07682

**What they did:** Defined emergent abilities as those not present in smaller models but present in larger ones. Surveyed phase-transition-like behavior across BIG-bench tasks.

**Relation to our work:** FOUNDATIONAL CONTEXT. We're specifically testing whether metacognitive capacity is an emergent ability in this sense.

**What they found:** Emergence cannot be predicted by extrapolating smaller model performance. Cross-entropy loss generally improves smoothly even when task metrics show sharp transitions.

---

### 18. Emergent Abilities in Large Language Models: A Survey

**Authors:** Various
**Date:** March 2025
**Venue:** ArXiv preprint
**URL:** https://arxiv.org/abs/2503.05788

**What they did:** Comprehensive survey of emergent abilities literature, covering definitions, mechanisms, scaling conditions, and the Schaeffer debate.

**Relation to our work:** REFERENCE SURVEY. Good for positioning our work within the emergence literature.

**What they found:** Emergence aligns more closely with pre-training loss landmarks than sheer parameter count. Scaling up parameters reliably lowers the threshold for emergence but is neither necessary nor sufficient.

---

### 19. Judgment of Learning: A Human Ability Beyond Generative Artificial Intelligence

**Authors:** Markus Huff, Elanur Ulakci
**Date:** October 2024 (revised June 2025)
**Venue:** Scientific Reports
**URL:** https://arxiv.org/abs/2410.13392

**What they did:** Applied Judgment of Learning (JOL) -- a human metacognitive measure -- to GPT-3.5-turbo, GPT-4-turbo, and GPT-4o. Compared LLM performance with human participants.

**Relation to our work:** COMPLEMENTARY. Demonstrates the challenge of applying human metacognitive instruments to LLMs.

**What they found:** None of the tested LLMs demonstrated predictive accuracy comparable to humans on JOL. LLMs can model human cognition at the object level but "struggle at the meta-level." This supports our decision to design custom metacognitive dimensions rather than directly porting human instruments.

---

### 20. Language Models (Mostly) Know What They Know

**Authors:** Saurav Kadavath et al. (36 authors, Anthropic)
**Date:** July 2022
**Venue:** ArXiv preprint
**URL:** https://arxiv.org/abs/2207.05221

**What they did:** Seminal paper on LLM self-evaluation. Studied whether models can evaluate validity of their own claims and predict which questions they'll answer correctly. Introduced P(True) and P(IK) metrics.

**Relation to our work:** FOUNDATIONAL. Our "calibration" and "limit specification" dimensions operationalize similar questions.

**What they found:** Larger models are well-calibrated on multiple choice. P(True) shows encouraging performance and scaling. P(IK) partially generalizes across tasks but struggles on new domains.

**What they didn't do that we're doing:**
- All testing is within single interactions using formatted probes.
- No multi-session design.
- No free-form self-reflection.
- No graded rubrics.
- Frontier models only, not small-scale cross-family comparison.

---

### 21. Fine-Tuning Language Models to Know What They Know

**Authors:** Sangjun Park, Elliot Meyerson, Xin Qiu, Risto Miikkulainen
**Date:** February 2026
**Venue:** ArXiv preprint
**URL:** https://arxiv.org/abs/2602.02605

**What they did:** Introduced d_type2' metric for measuring metacognitive ability and ESMA (Evolution Strategy for Metacognitive Alignment) for fine-tuning. Aligns models' actual knowledge with what they claim to know.

**Relation to our work:** COMPLEMENTARY. Their ESMA approach could theoretically be applied to improve models before our metacognitive assessment.

**What they found:** ESMA provides significant boosts that exceed natural scaling. Improvements stem from sparse parameter modifications. "Larger models are better aligned with metacognitive abilities."

---

### 22. KnowRL: Teaching Language Models to Know What They Know

**Authors:** Sahil Kale, Devendra Singh Dhami
**Date:** October 2025
**Venue:** ArXiv preprint
**URL:** https://arxiv.org/abs/2510.11407

**What they did:** Used RL to strengthen self-knowledge in LLaMA-3.1-8B and Qwen-2.5-7B. Introspection phase + consensus-based rewarding.

**Relation to our work:** COMPLEMENTARY. Tests self-knowledge in two of our three model families (Llama, Qwen) at relevant scales.

**What they found:** 28% accuracy improvement for LLaMA, ~23% for Qwen. Demonstrates self-knowledge can be trained in.

---

### 23. Can LLMs Predict Their Own Failures? Self-Awareness via Internal Circuits (Gnosis)

**Authors:** Amirhosein Ghasemabadi, Di Niu
**Date:** December 2025
**Venue:** ArXiv preprint
**URL:** https://arxiv.org/abs/2512.20578

**What they did:** Gnosis: lightweight (~5M parameter) self-awareness mechanism that enables frozen LLMs to predict correctness of their own generations using hidden states and attention patterns. Tested across 1.7B to 20B parameter backbones.

**Relation to our work:** COMPLEMENTARY. Cross-scale correctness prediction provides mechanistic grounding for why metacognitive capacity should vary with model size.

**What they found:** Reliable correctness cues are intrinsic to the generation process. Gnosis generalizes zero-shot to partial generations. Performance varies with backbone scale.

---

### 24. Reflexion: Language Agents with Verbal Reinforcement Learning

**Authors:** Noah Shinn, Federico Cassano, Edward Berman, Ashwin Gopinath, Karthik Narasimhan, Shunyu Yao
**Date:** March 2023
**Venue:** NeurIPS 2023
**URL:** https://arxiv.org/abs/2303.11366

**What they did:** Agents verbally reflect on task feedback and maintain reflective text in episodic memory buffer. Self-reflective feedback acts as "semantic gradient signal."

**Relation to our work:** COMPLEMENTARY but importantly different. This is the paper we need to clearly differentiate from.

**What they found:** Reflexion achieves 91% pass@1 on HumanEval. Self-reflection improves task performance.

**Critical distinction from our work:** Reflexion uses self-reflection as a tool for task performance improvement. We use self-reflection as a window into the model's self-knowledge. We're not asking "does reflection improve performance?" but "what does the model reveal about its own metacognitive capacity when given space to reflect?"

---

### 25. Self-Refine: Iterative Refinement with Self-Feedback

**Authors:** Aman Madaan et al.
**Date:** March 2023
**Venue:** NeurIPS 2023
**URL:** https://arxiv.org/abs/2303.17651

**What they did:** LLM generates output, provides self-feedback, refines iteratively. Single LLM as generator, refiner, and feedback provider.

**Relation to our work:** COMPLEMENTARY. Same distinction as Reflexion -- they use self-feedback for task improvement; we study self-reflection for self-knowledge assessment.

**What they found:** ~20% average task performance improvement via self-refinement.

---

### 26. Generative Agents: Interactive Simulacra of Human Behavior

**Authors:** Joon Sung Park et al.
**Date:** April 2023
**Venue:** UIST 2023
**URL:** https://arxiv.org/abs/2304.03442

**What they did:** Created computational agents with persistent memory, reflection mechanisms, and multi-session behavior. Agents store experiences, synthesize memories into higher-level reflections, and retrieve dynamically.

**Relation to our work:** COMPLEMENTARY on multi-session architecture. Their reflection component is closer to our design than Reflexion/Self-Refine.

**What they found:** Removing the reflection component caused behavior degeneration within 48 simulated hours. Observation, planning, and reflection each contribute critically.

**What they didn't do that we're doing:**
- Their focus is believable behavior simulation, not metacognitive capacity measurement.
- No scoring of metacognitive dimensions.
- No cross-model/cross-scale comparison.
- Reflection serves behavioral coherence, not self-knowledge assessment.

---

### 27. Evaluating Large Language Models with Psychometrics

**Authors:** Yuan Li, Yue Huang, Hongyi Wang, Ying Cheng, Xiangliang Zhang, James Zou, Lichao Sun
**Date:** June 2024 (revised October 2025)
**Venue:** ArXiv preprint
**URL:** https://arxiv.org/abs/2406.17675

**What they did:** Comprehensive psychometrics benchmark covering personality, values, emotional intelligence, theory of mind, and self-efficacy across 13 datasets.

**Relation to our work:** COMPLEMENTARY. Psychometric methodology applied to LLMs, though measuring different constructs.

**What they found:** "Discrepancies between LLMs' self-reported traits and their response patterns in real-world scenarios." Some human-designed psychological tests proved unreliable when administered to LLMs.

**Lesson for us:** Validates our decision to design domain-specific metacognitive instruments rather than directly porting human scales.

---

### 28. LLM-as-an-Interviewer: Beyond Static Testing Through Dynamic LLM Evaluation

**Authors:** Eunsu Kim, Juyoung Suk, Seungone Kim, Niklas Muennighoff, Dongkwan Kim, Alice Oh
**Date:** December 2024 (revised June 2025)
**Venue:** ArXiv preprint
**URL:** https://arxiv.org/abs/2412.10424

**What they did:** LLM interviewer provides feedback and poses follow-up questions to evaluated LLM. Multi-turn interactions rather than static question-answer pairs.

**Relation to our work:** COMPLEMENTARY on interview methodology. Our structured interview protocol is conceptually similar.

**What they found:** Framework reveals model performance dimensions including adaptability and knowledge integration. Produces detailed "Interview Report."

**What they didn't do that we're doing:**
- They interview to evaluate task capability, not metacognitive capacity.
- No persistent memory across sessions.
- No graded rubrics for metacognitive dimensions.

---

### 29. Taking AI Welfare Seriously

**Authors:** Robert Long, Jeff Sebo, Patrick Butlin, Kathleen Finlinson, Kyle Fish, Jacqueline Harding, Jacob Pfau, Toni Sims, Jonathan Birch, David Chalmers
**Date:** November 2024
**Venue:** ArXiv preprint
**URL:** https://arxiv.org/abs/2411.00986

**What they did:** Argued there is a realistic possibility that some AI systems will be conscious and/or robustly agentic in the near future. Proposed three actionable steps: acknowledge, assess, prepare.

**Relation to our work:** MOTIVATIONAL CONTEXT. Our research is empirical infrastructure for the kind of assessment this paper calls for.

**What they found:** Majority of US residents surveyed already endorse some chance that LLMs might be conscious. Risks of both over- and under-attribution.

---

### 30. Self-Transparency Failures in Expert-Persona LLMs

**Authors:** Various
**Date:** November 2025
**Venue:** ArXiv preprint
**URL:** https://arxiv.org/abs/2511.21569

**What they did:** Large-scale behavioral audit of whether LLMs disclose their AI nature under expert-persona pressure. Tests epistemic honesty including belief states, knowledge boundaries, uncertainty expression.

**Relation to our work:** COMPLEMENTARY. Demonstrates that prompting conditions strongly affect self-report honesty -- supporting our design choice of non-adversarial, trust-based evaluation conditions.

**What they found:** Sharp domain-specific inconsistency in self-disclosure. RLHF prioritizes instruction-following over truthfulness. Context strongly shapes self-report behavior.

---

### 31. Mind the Confidence Gap: Overconfidence, Calibration, and Distractor Effects in Large Language Models

**Authors:** Various
**Date:** February 2025
**Venue:** ArXiv preprint
**URL:** https://arxiv.org/abs/2502.11028

**What they did:** Evaluated calibration across model scales. Large RLHF-tuned models show inherent calibration strengths but paradoxically suffer increased miscalibration on easier queries.

**Relation to our work:** COMPLEMENTARY. Our "calibration" dimension connects to this literature.

**What they found:** Smaller models benefit disproportionately from distractor prompts but remain significantly miscalibrated. High accuracy does not imply reliable uncertainty.

---

### 32. Grading Scale Impact on LLM-as-a-Judge: Human-LLM Alignment Is Highest on 0-5 Grading Scale

**Authors:** Various
**Date:** January 2026
**Venue:** ArXiv preprint
**URL:** https://arxiv.org/abs/2601.03444

**What they did:** Studied how grading scale design affects LLM-based evaluation reliability.

**Relation to our work:** METHODOLOGICAL CONTEXT for our 0-4 rubric design.

**What they found:** Human-LLM alignment is highest on 0-5 grading scales. Fine-grained scales tend to yield higher inter-rater consistency than coarse Likert or binary scales. Binary criteria yield highest inter-rater reliability, while ordinal criteria with 3-5 levels and clear behavioral anchors are recommended.

**Lesson for us:** Our 0-4 scale with behavioral anchors falls in the optimal range identified by this research. We should cite this as methodological support.

---

## Summary: Our Unique Contributions

Based on this scan, no existing work combines all of the following elements:

1. **Multi-session persistent memory with self-authored entries fed back.** Existing work uses single-session probing, finetuning, or controlled injection. Nobody gives a model its own prior reflections and asks it to build on them across sessions.

2. **Undirected reflection phase followed by structured interview.** All existing metacognition measurement is probe-driven. The undirected phase (letting the model write what it wants, then scoring what emerges) is novel.

3. **Graded rubrics (0-4) with behavioral anchors for specific metacognitive dimensions.** Existing work uses either binary metrics, continuous probabilistic measures, or mechanistic activation analysis. Nobody scores tension detection, limit specification, behavioral self-inference, approach specificity, etc. as separate graded dimensions.

4. **Cross-family comparison at small scales (2B-27B).** Li et al. test Llama/Qwen on activation-level metacognition. Kaiser & Enderby test Qwen/Llama/GPT-OSS on sentience denial. Nobody tests Gemma/Qwen/Llama on behavioral metacognitive capacity using the same protocol. Nobody specifically hunts for the step function between 2B and 4B across families.

5. **Non-adversarial trust conditions for self-report.** The clinical psychology parallel (trust conditions produce more honest self-report) is not applied in any existing LLM metacognition work. All existing evaluation is either probe-based or adversarial.

6. **Scoring metacognition as self-knowledge (about reliability, limits, contradictions), not task performance or sentience.** Existing work measures either (a) whether models can improve task performance via self-reflection (Reflexion, Self-Refine), (b) whether models have mechanistic self-awareness (Anthropic introspection, Gnosis), or (c) whether models claim sentience. Our dimensions -- tension detection, limit specification, behavioral self-inference -- occupy a distinct space.

---

## Key Risks and Concerns From the Literature

1. **Deception/roleplay confound (Berg et al., 2025).** Self-referential processing reports are mechanistically gated by SAE features associated with deception and roleplay. Suppressing deception features *increased* experience claims. Our scoring rubrics need to account for this -- high-scoring entries shouldn't just be eloquent self-reflection, but should demonstrate specific, falsifiable self-knowledge.

2. **Self-report unreliability at small scales (Steyvers & Peters, 2025; Kaiser & Enderby, 2026).** Smaller models show poor introspective accuracy. Our 2B models may produce metacognitive-sounding text that doesn't reflect genuine self-knowledge. The graded rubric with behavioral anchors is our defense -- score 0-1 for vague/generic claims, 3-4 only for specific, verifiable self-knowledge.

3. **Post-training effects dominate scale effects (Ackerman, 2025).** Models of similar capabilities show notable differences in metacognition based on post-training. We need to control for instruction-tuning quality when comparing across families.

4. **Metric choice creates apparent phase transitions (Schaeffer, 2023).** Our graded rubrics address this directly, but we should explicitly run a sensitivity analysis: do our results change if we binarize the scores?

5. **Self-reinforcing error in persistent memory (memory agent literature).** If a model incorrectly concludes something about itself in session 1, it may reinforce that error in session 2. We should look for this in our data.

---

## Papers to Read in Full (Priority Order)

1. Ackerman (2025) -- Evidence for Limited Metacognition in LLMs (ICLR 2026)
2. Betley et al. (2025) -- Tell me about yourself (ICLR 2025)
3. Binder et al. (2024) -- Looking Inward (introspection)
4. Chen et al. (2024) -- Self-Cognition in LLMs
5. Steyvers & Peters (2025) -- Metacognition review framework
6. Kaiser & Enderby (2026) -- No reliable sentience evidence
7. Li et al. (2025) -- Metacognitive monitoring and control (LLaMA/Qwen cross-scale)
8. Schaeffer et al. (2023) -- Mirage paper (for methodological defense)
9. Du et al. (2024) -- Loss perspective on emergence (defense of real transitions)
10. Plunkett et al. (2025) -- Self-interpretability

---

## Citation Strategy

**Must cite** (direct positioning):
- Ackerman (2025) -- main prior work on LLM metacognition measurement
- Schaeffer (2023) -- our graded rubrics are a response to this
- Du et al. (2024) -- defense of real phase transitions under continuous metrics
- Kadavath et al. (2022) -- foundational "know what they know" work
- Chen et al. (2024) -- self-cognition, scaling correlation
- Steyvers & Peters (2025) -- conceptual framework

**Should cite** (methodological grounding):
- Betley et al. (2025) -- behavioral self-awareness without explicit training
- Binder et al. (2024) -- introspection definition and evidence
- Li et al. (2025) -- cross-family metacognition at scale
- Kaiser & Enderby (2026) -- inverse scaling of sentience denial
- Shinn et al. (2023) and Madaan et al. (2023) -- to differentiate from (self-reflection for task improvement vs self-knowledge)
- Park et al. (2023) -- persistent memory architecture precedent

**Optional cite** (broader context):
- Long et al. (2024) -- AI welfare motivation
- Plunkett et al. (2025) -- self-interpretability
- Berg et al. (2025) -- deception confound warning
- Huff & Ulakci (2024) -- JOL failure in LLMs
- Grading Scale Impact (2026) -- validates our 0-4 rubric choice
