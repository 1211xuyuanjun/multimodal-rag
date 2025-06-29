# 多模态RAG系统全面功能演示结果

演示时间: 2025-06-28 16:17:05

## 1. 文档处理功能

### 文档处理结果

```json
{
  "success": [
    "detective.pdf"
  ],
  "failed": [],
  "total_chunks": 104
}
```

### 存储信息

```json
{
  "storage_path": "./demo_storage",
  "text_count": 60,
  "image_count": 44,
  "total_count": 104,
  "config": {
    "embedding_dim": 1536,
    "index_type": "HNSW",
    "metric": "cosine",
    "nlist": 100,
    "m": 16,
    "ef_construction": 200,
    "ef_search": 100
  }
}
```

## 2. 智能查询分析

### 查询1分析

```json
{
  "原始查询": "这个故事的主人公是谁？",
  "分析结果": {
    "original_query": "这个故事的主人公是谁？",
    "intent_analysis": {
      "intent_type": "simple",
      "complexity_score": 2.0,
      "key_concepts": [
        "故事",
        "主人公"
      ],
      "question_type": "factual",
      "requires_decomposition": false,
      "reasoning": "该查询旨在获取一个明确的事实信息，即某个故事的主人公是谁。问题中仅涉及两个主要概念：'故事'和'主人公'，且逻辑关系简单，不需要复杂的推理或多方面的分析。因此复杂度较低，无需分解。"
    },
    "decomposition": {
      "sub_queries": [
        {
          "query": "这个故事的主人公是谁？",
          "intent": "simple",
          "priority": 1,
          "depends_on": null,
          "context_needed": false
        }
      ],
      "execution_plan": [
        0
      ]
    }
  }
}
```

### 查询2分析

```json
{
  "原始查询": "比较故事中不同角色的性格特点和动机",
  "分析结果": {
    "original_query": "比较故事中不同角色的性格特点和动机",
    "intent_analysis": {
      "intent_type": "comparative",
      "complexity_score": 8.0,
      "key_concepts": [
        "故事",
        "角色",
        "性格特点",
        "动机"
      ],
      "question_type": "comparative",
      "requires_decomposition": true,
      "reasoning": "该查询要求比较故事中不同角色的性格特点和动机，涉及对多个角色的分析与对比。需要分别识别各个角色的性格特征及其背后的动机，并进行横向比较，因此属于比较性问题，意图类型为comparative。关键概念包括‘故事’、‘角色’、‘性格特点’和‘动机’。由于涉及多方面分析且逻辑关系较复杂，复杂度评分为8分，需要分解为更小的问题来逐一处理。"
    },
    "decomposition": {
      "sub_queries": [
        {
          "query": "故事中主要角色有哪些？",
          "intent": "确定故事中需要比较的主要角色列表",
          "priority": 1,
          "depends_on": [],
          "context_needed": false
        },
        {
          "query": "每个主要角色的性格特点是什么？",
          "intent": "收集每个角色的具体性格特征，如勇敢、狡猾、忠诚等",
          "priority": 2,
          "depends_on": [
            0
          ],
          "context_needed": true
        },
        {
          "query": "每个主要角色的背景和动机是什么？",
          "intent": "了解每个角色的行为动机及其背后的驱动因素，例如复仇、权力、爱或生存",
          "priority": 3,
          "depends_on": [
            0
          ],
          "context_needed": true
        },
        {
          "query": "不同角色的性格如何影响他们的决策和行为？",
          "intent": "分析性格特点如何在情节发展中引导角色的选择",
          "priority": 4,
          "depends_on": [
            1,
            2
          ],
          "context_needed": true
        },
        {
          "query": "不同角色的动机如何导致冲突或合作？",
          "intent": "探讨角色之间的互动如何由其动机所塑造，并与整体情节发展联系起来",
          "priority": 5,
          "depends_on": [
            2,
            3
          ],
          "context_needed": true
        }
      ],
      "execution_plan": [
        0,
        1,
        2,
        3,
        4
      ]
    }
  }
}
```

### 查询3分析

```json
{
  "原始查询": "分析这个侦探故事的情节发展、推理过程和结局",
  "分析结果": {
    "original_query": "分析这个侦探故事的情节发展、推理过程和结局",
    "intent_analysis": {
      "intent_type": "multi_aspect",
      "complexity_score": 8.0,
      "key_concepts": [
        "侦探故事",
        "情节发展",
        "推理过程",
        "结局"
      ],
      "question_type": "analytical",
      "requires_decomposition": true,
      "reasoning": "该查询要求对侦探故事的多个方面进行深入分析，包括情节如何展开、推理的逻辑链条以及结局的合理性。涉及多个关键概念，并需要理解它们之间的逻辑关系。因此，这是一个分析性问题，且复杂度较高，需要分解为多个子问题来分别处理。"
    },
    "decomposition": {
      "sub_queries": [
        {
          "query": "侦探故事的主要情节发展阶段及其关键事件是什么？",
          "intent": "分析侦探故事的情节发展，明确各个阶段的关键事件和转折点。",
          "priority": 1,
          "depends_on": [],
          "context_needed": false
        },
        {
          "query": "侦探在故事中是如何推理并逐步揭示线索的？",
          "intent": "了解侦探在故事中的推理过程，包括使用的逻辑方法、发现的关键线索以及推理链。",
          "priority": 2,
          "depends_on": [
            0
          ],
          "context_needed": true
        },
        {
          "query": "侦探故事的结局如何揭示真相并解决案件？",
          "intent": "获取关于故事结局的信息，特别是案件真相的揭示方式以及主要人物的命运。",
          "priority": 3,
          "depends_on": [
            1
          ],
          "context_needed": true
        },
        {
          "query": "侦探故事的结局是否与之前的推理过程保持一致？",
          "intent": "验证结局与推理过程之间的逻辑一致性，确保没有矛盾或突兀的发展。",
          "priority": 4,
          "depends_on": [
            1,
            2
          ],
          "context_needed": true
        },
        {
          "query": "侦探故事的整体结构如何体现情节发展、推理和结局之间的联系？",
          "intent": "综合理解整个故事的结构，评估情节发展、推理过程和结局之间的连贯性与整体叙事效果。",
          "priority": 5,
          "depends_on": [
            0,
            1,
            2,
            3
          ],
          "context_needed": true
        }
      ],
      "execution_plan": [
        0,
        1,
        2,
        3,
        4
      ]
    }
  }
}
```

### 查询4分析

```json
{
  "原始查询": "如何从这个故事中学习推理技巧和逻辑思维方法？",
  "分析结果": {
    "original_query": "如何从这个故事中学习推理技巧和逻辑思维方法？",
    "intent_analysis": {
      "intent_type": "complex",
      "complexity_score": 8.0,
      "key_concepts": [
        "故事",
        "推理技巧",
        "逻辑思维方法",
        "学习"
      ],
      "question_type": "analytical",
      "requires_decomposition": true,
      "reasoning": "该查询要求从一个故事中提取抽象的技能（如推理技巧和逻辑思维方法），这需要对故事内容进行深入分析，并理解如何将其与认知技能的发展联系起来。问题不仅涉及对故事情节的理解，还需要进一步思考如何从中归纳出可应用的思维方法。因此，这是一个具有较高复杂度的分析性问题，需要分解为多个步骤：1）理解故事的内容与结构；2）识别其中体现的推理和逻辑模式；3）将这些模式转化为可学习的思维技巧。"
    },
    "decomposition": {
      "sub_queries": [
        {
          "query": "这个故事中有哪些情节或事件展示了推理技巧的应用？",
          "intent": "识别故事中与推理相关的具体情节，以理解推理技巧的表现形式。",
          "priority": 1,
          "depends_on": [],
          "context_needed": false
        },
        {
          "query": "这些推理技巧包括哪些具体的逻辑方法（如归纳、演绎、假设验证等）？",
          "intent": "分析故事中使用了哪些逻辑思维方法，以便明确学习的重点内容。",
          "priority": 2,
          "depends_on": [
            0
          ],
          "context_needed": true
        },
        {
          "query": "如何在现实生活中应用类似的故事中的逻辑思维方法？",
          "intent": "探索将故事中学到的逻辑方法迁移到实际问题解决中的方式。",
          "priority": 3,
          "depends_on": [
            1
          ],
          "context_needed": true
        },
        {
          "query": "有哪些阅读或学习策略可以用来从叙事性文本中提取推理技巧？",
          "intent": "总结有效的方法和技巧，帮助系统化地从故事中学习推理能力。",
          "priority": 4,
          "depends_on": [],
          "context_needed": false
        },
        {
          "query": "是否存在基于故事的学习资源或训练工具，用于提升逻辑推理能力？",
          "intent": "寻找可用于练习和强化通过故事学习推理技巧的实际资源或工具。",
          "priority": 5,
          "depends_on": [
            3
          ],
          "context_needed": true
        }
      ],
      "execution_plan": [
        0,
        1,
        2,
        3,
        4
      ]
    }
  }
}
```

## 3. 智能查询处理

### 查询1结果

```json
{
  "查询": "这个侦探故事的主要情节是什么？",
  "答案": "In this paper, to overcome these challenges, we revisit AI-generated text detection and approach\nthe problem from a fresh perspective.Individual authors invariably exhibit unique writing styles,\ncollectively constituting a vast feature space of writing styles.Our key insight is that an LLM can\nbe vi\n\nAI-generated text detection, wherein we carefully devise a multi-task auxiliary, multi-level contrastive loss to learn fine-grained features for distinguishing various writing styles.• We present Training-Free Incremental Adaptation (TFIA), a key feature of our method.Utilizing a modest amount of OO\n\n(TFIA), an efficient and effective strategy that leverages our method’s generalization capability to handle out-of-distribution (OOD) data.3.1 Framework Overview In this work, we focus on the task of AI-generated text detection.Given a query text x with L tokens,\nx = {w1, w2, ..., wL}, we aim to det",
  "处理信息": {
    "decomposition_used": false,
    "synthesis_used": false,
    "total_sub_queries": 1,
    "total_results": 5
  },
  "查询类型": "simple",
  "子查询": [
    {
      "query": "这个侦探故事的主要情节是什么？",
      "intent": "simple",
      "priority": 1,
      "results_count": 5
    }
  ]
}
```

### 查询2结果

```json
{
  "查询": "分析故事中的主要角色及其关系",
  "答案": "根据提供的子查询和相关信息，我们可以逐步分析并回答原始问题“**分析故事中的主要角色及其关系**”。以下是基于所有子查询信息的综合分析：\n\n---\n\n### 一、主要角色识别（基于子查询1）\n\n从文档内容来看，这并非传统意义上的叙事性文学作品，而是一篇关于**AI生成文本检测**的研究论文。因此，“角色”在这里并不指代传统意义上的人物角色，而是指参与AI生成与检测任务的各种模型和人类写作风格。\n\n#### 主要“角色”包括：\n1. **LLM（大语言模型）**\n- 包括 GPT-3.5、GPT-4、LLaMA、Claude 等具体模型。\n2. **人类写作者（Human）**\n- 作为对比对象，代表非AI生成文本的来源。\n3. **Encoder（编码器）**\n- 负责提取文本特征，是整个检测系统的核心组成部分。\n4. **KNN分类器**\n- 在推理阶段用于比对文本嵌入相似性，辅助判断文本来源。\n5. **Contrastive Loss 模块**\n- 一种训练策略，用于增强模型区分不同写作风格的能力。\n\n这些“角色”在技术层面上构成了一个完整的AI文本检测系统。\n\n---\n\n### 二、角色背景与性格特征（基于子查询2）\n\n由于这是技术文档，角色并无传统意义上的“性格”，但可以从功能角度描述其特性：\n\n| 角色 | 功能/特点 |\n|------|-----------|\n| LLM（如GPT系列、LLaMA等） | 表现出特定写作模式，具有一定的风格一致性，是检测系统的识别目标 |\n| 人类写作者 | 写作行为自然、多变，具备高度个性化特征 |\n| Encoder | 提取文本深层语义特征，负责将文本映射为可比较的向量表示 |\n| KNN分类器 | 基于已有数据库进行最近邻匹配，辅助分类决策 |\n| Contrastive Loss模块 | 驱动模型学习区分不同来源文本的细粒度特征 |\n\n这些角色共同协作，构建了一个能够识别AI生成文本的系统。\n\n---\n\n### 三、角色之间的关键互动事件（基于子查询3）\n\n从技术流程来看，这些“角色”之间存在以下关键交互：\n\n1. **文本输入 → Encoder**\n- 所有文本（无论是人类还是AI生成）都会被编码器转化为特征向量。\n\n2. **Encoder → Contrastive Loss模块**\n- 编码后的特征通过对比学习机制进行优化，强化模型对不同风格的区分能力。\n\n3. **Encoder输出 → KNN分类器**\n- 在推理阶段，编码后的文本与数据库中已知来源的文本进行相似性比对，辅助判断当前文本的来源。\n\n4. **LLM vs Human**\n- 这是整个检测任务的核心对比对象，模型需要学会区分这两类写作风格。\n\n5. **多任务辅助训练**\n- 多个任务协同训练，提升模型泛化能力和准确性。\n\n---\n\n### 四、角色之间的关系类型（基于子查询4）\n\n虽然这不是传统的故事结构，但从系统架构的角度可以抽象出如下“关系类型”：\n\n| 关系 | 类型说明 |\n|------|----------|\n| Encoder 与 Contrastive Loss | 协同关系：前者提供特征，后者优化特征表示 |\n| Encoder 与 KNN分类器 | 数据流关系：前者输出供后者使用 |\n| LLM 与 Human | 对立关系：检测系统的目标是区分两者 |\n| 整体系统与OO数据（Out-of-distribution） | 泛化关系：系统需适应未见过的数据分布（TFIA机制实现） |\n\n---\n\n### 五、角色及关系如何推动“故事”的发展（基于子查询5）\n\n在本研究中，“故事”的发展指的是技术方法的设计与优化过程。各个“角色”及其关系共同推动了以下几个方面的发展：\n\n1. **提高检测精度**\n- 通过引入Contrastive Loss，系统能更准确地区分不同写作风格，从而提升AI文本检测的准确性。\n\n2. **增强模型泛化能力**\n- 利用TFIA（Training-Free Incremental Adaptation）机制，使模型无需重新训练即可适应新类型的文本（例如新的AI模型或写作风格）。\n\n3. **实现高效推理**\n- 结合KNN分类器与预存的特征数据库，使得推理过程快速且资源消耗低。\n\n4. **支持多模型检测**\n- 框架设计支持多种LLM（如GPT、LLaMA、Claude）与人类文本的统一处理，增强了系统的适用范围。\n\n---\n\n### 六、总结\n\n| 分析维度 | 内容总结 |\n|----------|-----------|\n| 主要角色 | LLM（GPT系列、LLaMA、Claude）、人类写作者、Encoder、KNN分类器、Con...",
  "处理信息": {
    "decomposition_used": true,
    "synthesis_used": true,
    "total_sub_queries": 5,
    "total_results": 19
  },
  "查询类型": "complex",
  "子查询": [
    {
      "query": "故事中有哪些主要角色？",
      "intent": "识别并列出故事中的所有主要角色",
      "priority": 1,
      "results_count": 5
    },
    {
      "query": "每个主要角色的背景和性格特征是什么？",
      "intent": "了解每个主要角色的基本设定和个性特点",
      "priority": 2,
      "results_count": 5
    },
    {
      "query": "主要角色之间有哪些关键的互动事件？",
      "intent": "识别主要角色之间的关键情节互动",
      "priority": 3,
      "results_count": 5
    },
    {
      "query": "主要角色之间的关系类型是什么（如敌对、友谊、亲情等）？",
      "intent": "分类描述角色之间的关系性质",
      "priority": 4,
      "results_count": 5
    },
    {
      "query": "这些角色及其关系如何推动故事的发展？",
      "intent": "分析角色关系对故事情节发展的整体影响",
      "priority": 5,
      "results_count": 5
    }
  ]
}
```

### 查询3结果

```json
{
  "查询": "这个故事想要传达什么主题和寓意？",
  "答案": "从提供的信息来看，这些内容并非来自一个传统意义上的“故事”，而是来自一篇关于人工智能（AI）研究的学术论文。该论文聚焦于**AI生成文本检测**（AI-generated text detection），并提出了一个创新的方法框架来解决这一问题。因此，所谓的“主题”和“寓意”需要从技术研究的角度进行解读，而非文学层面的隐喻。\n\n---\n\n### 一、故事中的主要人物经历与变化（子查询1）\n\n在本研究中，“人物”可以被理解为模型或算法组件。通过消融实验（ablation studies）可以看出：\n\n- **关键发现**：移除任何损失项都会导致性能下降，说明各组件对整体效果有重要作用。\n- **多级对比学习损失**（multi-level contrastive loss）是提升模型表现的重要因素。\n- 正样本不是单一实例，而是一个满足条件的正样本集合，这体现了方法上的创新。\n\n➡️ 这表明模型在不断优化与迭代中变得更加鲁棒和精细，象征着技术的进步与复杂性应对能力的增强。\n\n---\n\n### 二、核心冲突与矛盾（子查询2）\n\n研究的核心挑战在于：\n\n- **区分人类写作与AI生成文本之间的细微差异**。\n- AI生成文本日益逼真，使得传统的检测方法失效。\n- 模型需具备对未知领域（Unseen Domains）和新模型（Unseen Models）的泛化能力。\n\n➡️ 这种“人机界限模糊”的冲突，反映了当前AI发展带来的伦理与安全问题，也突出了研究的现实意义。\n\n---\n\n### 三、背景与环境设定（子查询3）\n\n研究背景设定在AI大模型（LLMs）快速发展的时代背景下：\n\n- **社会文化背景**：AI写作工具普及，文本真假难辨，引发对信息真实性的担忧。\n- **技术背景**：传统检测方法难以适应多样化的写作风格和不断进化的AI模型。\n\n➡️ 因此，这项研究具有高度现实性和紧迫性，回应了AI应用中出现的实际问题。\n\n---\n\n### 四、象征元素及其传达的信息（子查询4）\n\n虽然文中没有明显的文学象征，但以下技术设计可视为象征性表达：\n\n- **OOD数据比例变化对性能的影响图**（Figure 2）象征着模型面对未知世界时的适应力。\n- **UMAP降维可视化图**（Figure 3）象征着模型能够有效捕捉不同写作风格的结构特征。\n- **TFIA策略**象征一种无需重新训练即可适应新数据的能力，体现了一种“可持续智能”的理念。\n\n➡️ 这些图表不仅是实验结果的展示，也象征着研究目标——构建一个灵活、高效、通用的AI文本识别系统。\n\n---\n\n### 五、综合分析：主题与道德寓意（子查询5）\n\n#### 主题总结：\n\n- **核心主题**：如何在AI生成内容日益逼真的背景下，构建一种高效、通用且可扩展的AI文本检测机制。\n- **技术主题**：强调模型细粒度特征学习能力、多任务协同训练的重要性，以及对未知数据的适应能力。\n\n#### 道德寓意：\n\n- **警示作用**：提醒人们AI生成内容可能带来的信息误导风险，呼吁加强技术监管与真实性验证。\n- **责任意识**：研究者应致力于开发透明、可控的技术，防止AI滥用。\n- **适应与进化**：技术必须具备持续进化能力以应对未来挑战，反映了一种“技术伦理+技术进步”并重的理念。\n\n---\n\n### 总结\n\n这篇“故事”本质上是一篇技术论文，但它所传达的主题和寓意却具有深刻的现实意义。它不仅展示了AI文本检测领域的最新进展，更传递出一个重要的信息：**在AI高速发展的今天，我们不仅要追求技术的先进性，更要关注其对社会的真实影响，并通过负责任的研究推动技术向善发展。**\n\n如果将之比作一个寓言故事，那么它的主角是一位智慧的工匠，他打造了一把能分辨真假语言的钥匙，希望以此守护人类语言的真实性与信任的基石。",
  "处理信息": {
    "decomposition_used": true,
    "synthesis_used": true,
    "total_sub_queries": 5,
    "total_results": 21
  },
  "查询类型": "complex",
  "子查询": [
    {
      "query": "故事中主要人物的经历和变化是什么？",
      "intent": "识别故事中的关键角色发展，以帮助揭示潜在主题。",
      "priority": 1,
      "results_count": 5
    },
    {
      "query": "故事中的核心冲突和矛盾是什么？",
      "intent": "分析推动情节发展的主要冲突，以理解其背后想要表达的寓意。",
      "priority": 2,
      "results_count": 5
    },
    {
      "query": "故事发生在什么样的背景或环境中？",
      "intent": "了解故事的时代、文化或社会背景，以便更准确地解读其主题。",
      "priority": 3,
      "results_count": 5
    },
    {
      "query": "作者通过故事中的象征元素传达了哪些信息？",
      "intent": "识别故事中的象征手法及其所代表的意义，从而挖掘深层寓意。",
      "priority": 4,
      "results_count": 5
    },
    {
      "query": "综合故事内容，其可能的主题和道德寓意是什么？",
      "intent": "基于前几个子查询的结果，总结出故事的主要主题与寓意。",
      "priority": 5,
      "results_count": 5
    }
  ]
}
```

## 4. 配置管理

### 当前配置

```json
{
  "intelligent_processor": {
    "decomposer_config": {
      "decomposition_threshold": 4.0,
      "max_sub_queries": 5,
      "enable_context_passing": true,
      "min_query_length": 10
    },
    "executor_config": {
      "max_context_length": 1000,
      "context_overlap": 0.2,
      "enable_result_fusion": true
    },
    "synthesizer_config": {
      "max_synthesis_length": 2000,
      "enable_logical_flow": true,
      "include_source_references": true,
      "synthesis_style": "comprehensive"
    },
    "processor_config": {
      "enable_decomposition": true,
      "decomposition_threshold": 4.0,
      "max_sub_queries": 5,
      "enable_synthesis": true,
      "fallback_to_simple": true
    }
  },
  "query_optimizer": {
    "enable_query_expansion": true,
    "enable_query_rewrite": true,
    "enable_self_critique": true,
    "enable_llm_diversification": true,
    "max_expansions": 3,
    "expansion_methods": [
      "synonym",
      "related_terms",
      "context"
    ],
    "similarity_threshold": 0.7
  },
  "retriever": {
    "top_k": 10,
    "score_threshold": 0.7,
    "rerank_top_k": 5,
    "hybrid_weights": {
      "bm25": 0.3,
      "vector": 0.5,
      "multimodal": 0.2
    }
  }
}
```

### 简单查询结果

```json
{
  "查询": "这个故事的结局如何？",
  "答案": "参考资料中没有提到与“故事的结局”相关的信息。上述资料主要讨论的是关于AI生成文本检测的技术方法，包括使用对比学习和多任务学习框架来改进检测效果，并未涉及任何具体的故事或情节及其结局。\n\n如果您有其他关于AI生成文本检测的问题，请随时提出！\n\n## 参考来源\n- **detective.pdf** (第2页)\n- **detective.pdf** (第2页)\n- **detective.pdf** (第5页)\n- **detective.pdf** (第10页)"
}
```

### 智能查询结果

```json
{
  "查询": "这个故事的结局如何？",
  "答案": "In this paper, to overcome these challenges, we revisit AI-generated text detection and approach\nthe problem from a fresh perspective.Individual authors invariably exhibit unique writing styles,\ncollectively constituting a vast feature space of writing styles.Our key insight is that an LLM can\nbe vi\n\nFigure 2: Analysis of model performance changes with the addition of OOD data. The x-axis\nrepresents the proportion of OOD data added, and the y-axis represents the AvgRec metric. (a)\npresents the results for Unseen Models, and (b) for Unseen Domains.\nFigure 3: UMAP [45] dimensionality reduction vis\n\nresulting in 200K articles with 20 labels, detailed in Table 11.D Experiments on compatibility with diverse encoders The results of fine-tuning various text encoders using our approach are shown in Table 6.Table 6: Experimental results of applying our method to multiple text encoders on Cross-domain",
  "处理信息": {
    "decomposition_used": false,
    "synthesis_used": false,
    "total_sub_queries": 1,
    "total_results": 5
  }
}
```

## 5. 多模态功能

### 多模态查询1

```json
{
  "查询": "文档中有哪些图片或图表？",
  "答案": "AI-generated text detection, wherein we carefully devise a multi-task auxiliary, multi-level contrastive loss to learn fine-grained features for distinguishing various writing styles.• We present Training-Free Incremental Adaptation (TFIA), a key feature of our method.Utilizing a modest amount of OO\n\n(TFIA), an efficient and effective strategy that leverages our method’s generalization capability to handle out-of-distribution (OOD) data.3.1 Framework Overview In this work, we focus on the task of AI-generated text detection.Given a query text x with L tokens,\nx = {w1, w2, ..., wL}, we aim to det\n\nresulting in 200K articles with 20 labels, detailed in Table 11.D Experiments on compatibility with diverse encoders The results of fine-tuning various text encoders using our approach are shown in Table 6.Table 6: Experimental results of applying our method to multiple text encoders on Cross-domain",
  "检索结果数": 5
}
```

### 多模态查询2

```json
{
  "查询": "描述文档中的视觉元素",
  "答案": "resulting in 200K articles with 20 labels, detailed in Table 11.D Experiments on compatibility with diverse encoders The results of fine-tuning various text encoders using our approach are shown in Table 6.Table 6: Experimental results of applying our method to multiple text encoders on Cross-domain\n\n3,000 Italian - - 3,000 - - 3,000 3,000 Table 11: The number of data samples generated by each generator in TuringBench [61].Text Generator\nData samples\nHuman\n8,854\nGPT-1\n8,309\nGPT-2_small\n8,164\nGPT-2_medium\n8,164\nGPT-2_large\n8,164\nGPT-2_xl\n8,309\nGPT-2_PyTorch\n8,854\nGPT-3\n8,164\nGROVER_base\n8,854\nGRO\n\nrelationship should be satisfied: S(i, j) > S(i, k), ∀xj = 1, xk = 0.(2) Similarly, for text Ti(xi = 0) generated by LLMs, Ineq.1 suggests the existence of multi-level\nsimilarities and differences internally within LLMs, expressed as follows:\nS(i, j) > S(i, l) > S(i, m) > S(i, n), ∀zi = zj, zi ̸= zl",
  "检索结果数": 5
}
```

### 多模态查询3

```json
{
  "查询": "文档的布局和格式是怎样的？",
  "答案": "In this paper, to overcome these challenges, we revisit AI-generated text detection and approach\nthe problem from a fresh perspective.Individual authors invariably exhibit unique writing styles,\ncollectively constituting a vast feature space of writing styles.Our key insight is that an LLM can\nbe vi\n\nAI-generated text detection, wherein we carefully devise a multi-task auxiliary, multi-level contrastive loss to learn fine-grained features for distinguishing various writing styles.• We present Training-Free Incremental Adaptation (TFIA), a key feature of our method.Utilizing a modest amount of OO\n\n(TFIA), an efficient and effective strategy that leverages our method’s generalization capability to handle out-of-distribution (OOD) data.3.1 Framework Overview In this work, we focus on the task of AI-generated text detection.Given a query text x with L tokens,\nx = {w1, w2, ..., wL}, we aim to det",
  "检索结果数": 5
}
```

