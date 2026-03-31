# Course Management and Administration

## Overview

This chapter covers the day-to-day operations of managing courses within the LMS, including course creation, enrollment management, gradebook configuration, assignment and rubric setup, and discussion forum administration. These procedures assume that the system setup described in Chapter 01 has been completed and that the administrator has access to the LMS administration interface.

## Creating Courses

### Course Creation Workflow

To create a new course, navigate to Administration > Courses > Add New Course. Complete the following fields:

The course full name (displayed to students in the course catalog and dashboard), the course short name (used in navigation breadcrumbs and URLs --- keep to 10 characters or fewer using a department code and number format such as EDU7100), the course category (used for catalog organization and reporting --- create categories that mirror the institutional department structure), the course start date and end date (controls when the course appears in students' active course lists), the course format (topics, weekly, or social --- topics format is recommended for most courses as it provides the most flexible content organization), and the course visibility (visible, hidden from catalog but accessible via direct link, or completely hidden).

After creating the course shell, configure the following course-level settings:

| Setting | Recommended Configuration | Rationale |
|---|---|---|
| **Enrollment methods** | Manual enrollment by instructor + self-enrollment with key | Balances control and flexibility |
| **Guest access** | Disabled | Prevents unauthorized content access |
| **Groups** | Enabled, visible groups | Supports tutorial/lab sections within a course |
| **Completion tracking** | Enabled with activity completion | Enables progress monitoring and reporting |
| **File upload limit** | 20 MB per file | Prevents storage exhaustion; increase for media courses |
| **Number of sections** | Match the number of teaching weeks | Provides clear course structure |
| **Default section format** | Collapsed | Reduces cognitive overload on the course page |

### Course Templates

Create course templates for commonly offered course types to reduce setup time and ensure consistency. A template includes the course structure (sections, activities, resources), default settings, and placeholder content that instructors customize for their specific offering. Store templates in a dedicated "Template" category that is hidden from the student-facing catalog.

To create a template: build a fully configured course with all standard elements, navigate to the course backup tool, create a backup excluding user data and enrollment, and save the backup file to the template library. To deploy a template: create a new course shell, use the course restore tool to import the template backup, and adjust dates, instructor details, and section-specific content.

## Enrollment Management

### Enrollment Methods

The LMS supports multiple enrollment methods, which can be enabled simultaneously:

Manual enrollment allows administrators and instructors to add students directly by searching for user accounts and assigning a role. This method provides maximum control and is suitable for small courses, special-enrollment programs, and correcting enrollment errors.

Self-enrollment with an enrollment key allows students to enroll themselves using a password distributed by the instructor. This method scales well for large courses and reduces administrative workload. Set the enrollment key through Course Settings > Enrollment Methods > Self-Enrollment > Enrollment Key.

Cohort-based enrollment automatically enrolls all members of a defined cohort (such as a program intake group) into specified courses. This method is efficient for program-level enrollment where all students in a cohort take the same courses. Configure cohorts under Administration > Users > Cohorts.

External database enrollment synchronizes enrollment data from an external student information system (SIS). This method is essential for large institutions where enrollment is managed centrally. Configuration requires database connection credentials and a mapping table that links SIS course codes to LMS course IDs and SIS student IDs to LMS user accounts.

### Role Permissions

The LMS uses a role-based access control system. The following table summarizes the default permissions for each standard role:

| Permission | Student | Tutor | Instructor | Course Admin | Site Admin |
|---|---|---|---|---|---|
| View course content | Yes | Yes | Yes | Yes | Yes |
| Submit assignments | Yes | No | No | No | No |
| Grade assignments | No | Yes | Yes | Yes | Yes |
| Create activities | No | No | Yes | Yes | Yes |
| Manage enrollment | No | No | Yes | Yes | Yes |
| Edit course settings | No | No | Limited | Yes | Yes |
| Delete course | No | No | No | Yes | Yes |
| Access all courses | No | No | No | No | Yes |
| Manage user accounts | No | No | No | No | Yes |

> **Important:** Avoid modifying default role permissions unless absolutely necessary. Custom permission changes propagate across all courses and can create unintended access issues. Instead, create a custom role that inherits from a standard role and override only the specific permissions required.

## Gradebook Configuration

### Setting Up the Gradebook

Navigate to Course Administration > Gradebook Setup to configure the grade structure. The gradebook uses a hierarchical category system:

The top-level course total aggregates all grade categories. Each category (e.g., Assignments, Quizzes, Participation, Final Exam) contains individual grade items and uses an aggregation method to calculate the category total. Categories can be weighted to reflect their contribution to the overall course grade.

| Category | Weight | Aggregation Method | Drop Lowest | Notes |
|---|---|---|---|---|
| Assignments | 40% | Weighted mean | 1 of 6 | Drops lowest assignment score |
| Quizzes | 20% | Simple weighted mean | 2 of 10 | Drops two lowest quiz scores |
| Discussion participation | 10% | Simple weighted mean | 0 | All forums graded |
| Midterm exam | 10% | Natural (single item) | N/A | Single grade item |
| Final exam | 20% | Natural (single item) | N/A | Single grade item |

### Grade Scale Configuration

Configure grade scales to match institutional grading policies. The following table shows a common configuration:

| Grade | Percentage Range | Grade Point | Description |
|---|---|---|---|
| HD | 80-100% | 4.0 | High Distinction |
| D | 70-79% | 3.0 | Distinction |
| C | 60-69% | 2.0 | Credit |
| P | 50-59% | 1.0 | Pass |
| F | 0-49% | 0.0 | Fail |

Configure the grade display type (percentage, letter, or both) and the decimal places for grade display (1 decimal place is standard). Enable grade history tracking to maintain an audit trail of all grade changes.

## Assignment and Rubric Setup

### Creating Assignments

Navigate to the target course section and select Add Activity > Assignment. Configure the following settings:

The assignment name and description (include clear instructions, formatting requirements, and the evaluation criteria). The submission type (online text, file upload, or both). The maximum file size and number of files (match the course-level file upload limit or set a lower value). The due date, cutoff date (after which no submissions are accepted), and grade-to-by date (reminder for graders). The feedback type (comments, annotated PDF, offline grading worksheet, or rubric). The group submission settings if the assignment is collaborative.

### Rubric Design

Navigate to the assignment's advanced grading settings and select Rubric as the grading method. Build the rubric using the following structure:

Each rubric criterion represents a dimension of quality being assessed. Each criterion has a set of levels (typically 3-5) with descriptive text and a point value. The total rubric score is the sum of points across all criteria.

Design effective rubrics by ensuring that criterion descriptions are specific and observable (not vague qualities like "good" or "thorough"), that level descriptions clearly differentiate performance levels with concrete indicators, that the point distribution reflects the relative importance of each criterion, and that the rubric is shared with students before the assignment to clarify expectations.

| Criterion | Excellent (4) | Proficient (3) | Developing (2) | Beginning (1) |
|---|---|---|---|---|
| **Thesis clarity** | Thesis is specific, arguable, and clearly stated in the introduction | Thesis is present and mostly clear; minor ambiguity | Thesis is vague or too broad; requires inference | No identifiable thesis statement |
| **Evidence quality** | Multiple relevant, credible sources integrated with analysis | Adequate sources with some analysis | Limited sources or superficial use | No supporting evidence or unreliable sources |
| **Organization** | Logical structure with clear transitions between all sections | Generally organized; occasional gaps in flow | Inconsistent structure; several disjointed sections | No discernible organizational pattern |
| **Writing mechanics** | Error-free grammar, spelling, and formatting | Minor errors that do not impede understanding | Frequent errors that occasionally impede understanding | Pervasive errors that significantly impede understanding |

## Discussion Forum Management

### Forum Types and Configuration

The LMS supports several forum types for different pedagogical purposes:

Standard forums allow any participant to start new discussion threads and reply to existing ones. Use for open-ended discussion, Q&A, and peer interaction. Single-discussion forums contain a single thread to which all participants reply. Use for focused debate on a specific question or case study. Q&A forums require students to post their own response before they can view peers' responses. Use for ensuring independent thinking before peer exposure. Blog-like forums allow each student to create one thread to which others can reply. Use for reflective journals and portfolio-style activities.

Configure forum settings to match pedagogical intent:

| Setting | Discussion Forum | Q&A Forum | Reflective Journal |
|---|---|---|---|
| **Forum type** | Standard | Q&A | Blog-like |
| **Subscription** | Optional | Forced | Optional |
| **Attachment limit** | 3 files, 10 MB | 1 file, 5 MB | 5 files, 20 MB |
| **Word count minimum** | None | 150 words | 200 words |
| **Rating scale** | Not rated | 0-10 scale | 0-5 scale |
| **Post editing window** | 30 minutes | 30 minutes | Unlimited |
| **Display format** | Threaded | Nested | Flat (oldest first) |

### Moderation Procedures

Monitor discussion forums regularly for academic integrity issues (copied responses), inappropriate content, and off-topic posting. Use the flagging system to mark posts requiring review. Establish clear discussion guidelines in the course syllabus, including expectations for respectful discourse, citation requirements, and consequences for academic dishonesty.

For large courses with high forum activity, delegate moderation to teaching assistants assigned the Tutor role. Tutors can edit and delete student posts, split threads, and lock discussions, but cannot modify forum settings or grade configurations.

> **Tip:** Enable email digests for forums rather than individual post notifications. Individual notifications generate substantial email volume in active courses and lead to notification fatigue, causing students to disable notifications entirely and miss important updates.
